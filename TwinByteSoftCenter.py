import json
import math
import re
import sys
import time
import os
from pathlib import Path
from typing import Dict, List, Optional

import requests
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QEasingCurve, QLocale, QPropertyAnimation, QTimer, QPoint, pyqtProperty
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QMouseEvent, QRadialGradient
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QDialog,
    QFileDialog
)
from urllib.parse import unquote, urlparse

APP_NAME = "TwinByte SoftCenter"
BRANDING = "TwinByte IT"
VERSION = "2.0.2"
CONTACT_EMAIL = "twinbytecontact@gmail.com"
CACHE_FOLDER_NAME = "TwinByteSoftCenter"
DATA_FILE = "programs.json"
SETTINGS_FILE_NAME = "settings.json"
APP_ICON_FILE = "TwinByte_SoftCenter.ico"
TITLE_BAR_ICON_SIZE = 24  # px — размер иконки слева от названия в верхней полоске окна
ALLOWED_NAME_PARTS = ["twinbyte", "softcenter"]
TEMP_FOLDERS = ["temp", "tmp", "appdata", r"local\temp", "local/temp"]

CATEGORY_ICONS = {
    "all": "🗂️",
    "browsers": "🌐",
    "system": "🛠️",
    "optimization": "⚡",
    "diagnostics": "🩺",
    "security": "🛡️",
    "other": "🧩",
}
DEFAULT_CATEGORY_ICON = "📦"
FAVORITES_CATEGORY_ID = "__favorites__"

ACCENT_PALETTE = ["#00F0FF", "#7000FF", "#FF007A", "#00FF66", "#FFD700", "#9D00FF", "#00B8FF", "#FF3366"]

ICON_CACHE: Dict[str, QIcon] = {}
APP_ICON_PATH: Optional[Path] = None

def resolve_app_icon_path(resource_root: Path, app_root: Path) -> Optional[Path]:
    for candidate in (resource_root / APP_ICON_FILE, app_root / APP_ICON_FILE):
        if candidate.exists():
            return candidate
    return None

def get_brand_pixmap(size: int) -> QPixmap:
    # Uses the real TwinByte_SoftCenter.ico for the header logo / About dialog
    # when it's available; falls back to the generated "TB" badge otherwise.
    if APP_ICON_PATH is not None:
        pixmap = QIcon(str(APP_ICON_PATH)).pixmap(size, size)
        if not pixmap.isNull():
            return pixmap
    return create_icon(APP_NAME, QColor("#00E0FF"), letters="TB").pixmap(size, size)

LANGUAGES = ["ru", "en", "pl", "uk"]
LANGUAGE_LABELS = {"ru": "RU", "en": "EN", "pl": "PL", "uk": "UA"}
LANGUAGE_FLAGS = {"ru": "🇷🇺", "en": "🇬🇧", "pl": "🇵🇱", "uk": "🇺🇦"}

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "app_subtitle": {
        "ru": "Премиальный портативный центр от {brand}",
        "en": "Premium portable center by {brand}",
        "pl": "Ekskluzywne centrum przenośne od {brand}",
        "uk": "Преміальний портативний центр від {brand}",
    },
    "stats": {
        "ru": "⚡ {count} приложений · {cats} категорий · Ultra Portable",
        "en": "⚡ {count} apps · {cats} categories · Ultra Portable",
        "pl": "⚡ {count} aplikacji · {cats} kategorii · Ultra Portable",
        "uk": "⚡ {count} програм · {cats} категорій · Ultra Portable",
    },
    "about_button": {"ru": "Инфо", "en": "Info", "pl": "Info", "uk": "Інфо"},
    "settings_btn": {"ru": "Настройки", "en": "Settings", "pl": "Ustawienia", "uk": "Налаштування"},
    "language_tooltip": {"ru": "Язык интерфейса", "en": "Interface language", "pl": "Język interfejsu", "uk": "Мова інтерфейсу"},
    "search_placeholder": {
        "ru": "🔍 Найти программу...",
        "en": "🔍 Search program...",
        "pl": "🔍 Szukaj programu...",
        "uk": "🔍 Знайти програму...",
    },
    "categories_label": {"ru": "КАТЕГОРИИ", "en": "CATEGORIES", "pl": "KATEGORIE", "uk": "КАТЕГОРІЇ"},
    "all_programs": {"ru": "Все программы", "en": "All programs", "pl": "Wszystkie programy", "uk": "Усі програми"},
    "content_title_found": {
        "ru": "{category}  —  найдено {n}",
        "en": "{category}  —  found {n}",
        "pl": "{category}  —  znaleziono {n}",
        "uk": "{category}  —  знайдено {n}",
    },
    "empty_state": {
        "ru": "Ничего не найдено. Попробуйте изменить запрос.",
        "en": "Nothing found. Try changing your query.",
        "pl": "Nic nie znaleziono. Spróbuj zmienić zapytanie.",
        "uk": "Нічого не знайдено. Спробуйте інший запит.",
    },
    "download_button": {"ru": "Скачать", "en": "Download", "pl": "Pobierz", "uk": "Завантажити"},
    "status_copyright": {
        "ru": "© 2026 {brand}. Все права защищены.",
        "en": "© 2026 {brand}. All rights reserved.",
        "pl": "© 2026 {brand}. Wszelkie prawa zastrzeżone.",
        "uk": "© 2026 {brand}. Усі права захищено.",
    },
    "download_in_progress_title": {
        "ru": "Уже качаем",
        "en": "Already downloading",
        "pl": "Pobieranie trwa",
        "uk": "Вже завантажуємо",
    },
    "download_in_progress_text": {
        "ru": "Дождитесь завершения текущей загрузки.",
        "en": "Please wait for the current download to finish.",
        "pl": "Poczekaj na zakończenie bieżącego pobierania.",
        "uk": "Дочекайтеся завершення поточного завантаження.",
    },
    "error_title": {"ru": "Ошибка", "en": "Error", "pl": "Błąd", "uk": "Помилка"},
    "whitelist_error": {
        "ru": "Ссылка не в белом списке.",
        "en": "Link not in whitelist.",
        "pl": "Link zablokowany.",
        "uk": "Посилання заблоковано.",
    },
    "platform_error": {
        "ru": "Поддерживается только Windows.",
        "en": "Only Windows is supported.",
        "pl": "Tylko Windows jest obsługiwany.",
        "uk": "Підтримується лише Windows.",
    },
    "confirm_title": {"ru": "Загрузка", "en": "Download", "pl": "Pobieranie", "uk": "Завантаження"},
    "confirm_text": {
        "ru": "Сохранить {name} в Загрузки?\n\n{url}",
        "en": "Save {name} to Downloads?\n\n{url}",
        "pl": "Zapisać {name} w Pobranych?\n\n{url}",
        "uk": "Зберегти {name} у Завантаження?\n\n{url}",
    },
    "downloading_status": {
        "ru": "Загрузка: {name}...",
        "en": "Downloading: {name}...",
        "pl": "Pobieranie: {name}...",
        "uk": "Завантаження: {name}...",
    },
    "download_progress_status": {
        "ru": "Скачано: {percent}%  |  {speed}",
        "en": "Downloaded: {percent}%  |  {speed}",
        "pl": "Pobrano: {percent}%  |  {speed}",
        "uk": "Завантажено: {percent}%  |  {speed}",
    },
    "download_done_status": {
        "ru": "Успешно: {name}",
        "en": "Success: {name}",
        "pl": "Sukces: {name}",
        "uk": "Успішно: {name}",
    },
    "done_title": {"ru": "Готово", "en": "Done", "pl": "Gotowe", "uk": "Готово"},
    "done_text": {
        "ru": "Файл сохранён в:\n{path}",
        "en": "File saved to:\n{path}",
        "pl": "Plik zapisano w:\n{path}",
        "uk": "Файл збережено в:\n{path}",
    },
    "open_folder_btn": {"ru": "Папка", "en": "Folder", "pl": "Folder", "uk": "Папка"},
    "run_file_btn": {"ru": "Запуск", "en": "Run", "pl": "Uruchom", "uk": "Запуск"},
    "close_btn": {"ru": "Закрыть", "en": "Close", "pl": "Zamknij", "uk": "Закрити"},
    "download_error_status": {"ru": "Сбой", "en": "Failed", "pl": "Błąd", "uk": "Збій"},
    "download_error_text": {
        "ru": "Не удалось скачать:\n{error}",
        "en": "Download failed:\n{error}",
        "pl": "Pobieranie nie powiodło się:\n{error}",
        "uk": "Не вдалося завантажити:\n{error}",
    },
    "about_title": {"ru": "О программе", "en": "About", "pl": "O programie", "uk": "Про програму"},
    "about_html": {
        "ru": "<h2>{brand}</h2><p><strong>{app}</strong><br>Версия {version}</p><p>Премиальный центр загрузок.</p>",
        "en": "<h2>{brand}</h2><p><strong>{app}</strong><br>Version {version}</p><p>Premium download center.</p>",
        "pl": "<h2>{brand}</h2><p><strong>{app}</strong><br>Wersja {version}</p><p>Ekskluzywne centrum pobierania.</p>",
        "uk": "<h2>{brand}</h2><p><strong>{app}</strong><br>Версія {version}</p><p>Преміальний центр завантажень.</p>",
    },
    "launch_blocked_title": {"ru": "Блокировка", "en": "Blocked", "pl": "Zablokowane", "uk": "Блокування"},
    "launch_blocked_name_text": {
        "ru": "Имя файла или папки изменено. Запуск отменён.",
        "en": "File or folder name changed. Launch cancelled.",
        "pl": "Zmieniono nazwę pliku lub folderu. Uruchomienie anulowane.",
        "uk": "Ім'я файлу або папки змінено. Запуск скасовано.",
    },
    "launch_blocked_temp_text": {
        "ru": "Запуск из Temp запрещён. Распакуйте программу.",
        "en": "Launch from Temp blocked. Extract the app.",
        "pl": "Uruchomienie z Temp zablokowane. Wypakuj aplikację.",
        "uk": "Запуск із Temp заборонено. Розпакуйте програму.",
    },
    "catalog_missing_title": {"ru": "Пустой каталог", "en": "Empty catalog", "pl": "Pusty katalog", "uk": "Порожній каталог"},
    "catalog_missing_text": {
        "ru": "Ошибка чтения базы: {error}",
        "en": "Database read error: {error}",
        "pl": "Błąd odczytu bazy: {error}",
        "uk": "Помилка читання бази: {error}",
    },
    "crash_title": {"ru": "Упс, краш", "en": "Oops, crash", "pl": "Ups, awaria", "uk": "Упс, краш"},
    "crash_text": {
        "ru": "Критическая ошибка:\n{error}\nЗаписано в {logname}.",
        "en": "Critical error:\n{error}\nLogged to {logname}.",
        "pl": "Błąd krytyczny:\n{error}\nZapisano w {logname}.",
        "uk": "Критична помилка:\n{error}\nЗаписано в {logname}.",
    },
    "html_response_error": {
        "ru": "Сервер отдал HTML. Проверьте ссылку.",
        "en": "Server returned HTML. Check the link.",
        "pl": "Serwer zwrócił HTML. Sprawdź link.",
        "uk": "Сервер віддав HTML. Перевірте посилання.",
    },
    "settings_title": {"ru": "Настройки", "en": "Settings", "pl": "Ustawienia", "uk": "Налаштування"},
    "download_folder_lbl": {"ru": "Папка загрузок:", "en": "Download folder:", "pl": "Folder pobierania:", "uk": "Папка завантажень:"},
    "change_folder_btn": {"ru": "Изменить папку", "en": "Change folder", "pl": "Zmień folder", "uk": "Змінити папку"},
    "select_folder_dialog": {"ru": "Выберите папку для загрузок", "en": "Select download folder", "pl": "Wybierz folder pobierania", "uk": "Виберіть папку для завантажень"},
    "favorites_category": {"ru": "Избранное", "en": "Favorites", "pl": "Ulubione", "uk": "Обране"},
    "favorite_tooltip": {"ru": "В избранное", "en": "Add to favorites", "pl": "Do ulubionych", "uk": "До обраного"},
    "performance_mode_lbl": {"ru": "Режим производительности", "en": "Performance mode", "pl": "Tryb wydajności", "uk": "Режим продуктивності"},
    "performance_mode_hint": {
        "ru": "Отключает тени и анимации карточек — плавнее на слабых ПК",
        "en": "Disables card shadows/animations — smoother on weak PCs",
        "pl": "Wyłącza cienie/animacje kart — płynniej na słabszych PC",
        "uk": "Вимикає тіні/анімації карток — плавніше на слабких ПК",
    },
    "always_on_top_lbl": {"ru": "Поверх всех окон", "en": "Always on top", "pl": "Zawsze na wierzchu", "uk": "Поверх усіх вікон"},
    "on_lbl": {"ru": "Вкл", "en": "On", "pl": "Wł", "uk": "Увімк"},
    "off_lbl": {"ru": "Выкл", "en": "Off", "pl": "Wył", "uk": "Вимк"},
    "settings_restart_hint": {
        "ru": "Изменения применятся сразу",
        "en": "Changes apply immediately",
        "pl": "Zmiany zastosują się natychmiast",
        "uk": "Зміни застосуються одразу",
    },
}

class Translator:
    def __init__(self, lang: str = "ru"):
        self.lang = lang if lang in LANGUAGES else "ru"

    def set_language(self, lang: str) -> None:
        if lang in LANGUAGES:
            self.lang = lang

    def __call__(self, key: str, **kwargs) -> str:
        table = TRANSLATIONS.get(key, {})
        text = table.get(self.lang) or table.get("en") or table.get("ru") or (next(iter(table.values())) if table else key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text

tr = Translator()

def localized(value, lang: str) -> str:
    if isinstance(value, dict):
        if not value:
            return ""
        return value.get(lang) or value.get("en") or value.get("ru") or next(iter(value.values()))
    return value or ""

def detect_system_language() -> str:
    try:
        name = QLocale.system().name().lower()
    except Exception:
        name = ""
    for code in LANGUAGES:
        if name.startswith(code):
            return code
    return "ru"

def resource_path() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

def app_root_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.argv[0]).resolve().parent
    return Path(__file__).resolve().parent

def ensure_portable_cache(root: Path) -> Path:
    cache_dir = root / CACHE_FOLDER_NAME
    cache_dir.mkdir(exist_ok=True)
    return cache_dir

def is_temporary_location(path: Path) -> bool:
    normalized = str(path).lower().replace("/", "\\")
    return any(token in normalized for token in TEMP_FOLDERS)

def settings_path(root: Path) -> Path:
    return root / CACHE_FOLDER_NAME / SETTINGS_FILE_NAME

DEFAULT_SETTINGS = {
    "language": "",
    "performance_mode": False,
    "always_on_top": False,
    "favorites": [],
}

def load_app_settings(root: Path) -> Dict:
    path = settings_path(root)
    settings = dict(DEFAULT_SETTINGS)
    try:
        with open(path, "r", encoding="utf-8") as file:
            saved = json.load(file)
        if isinstance(saved, dict):
            if saved.get("language") in LANGUAGES:
                settings["language"] = saved["language"]
            settings["performance_mode"] = bool(saved.get("performance_mode", False))
            settings["always_on_top"] = bool(saved.get("always_on_top", False))
            favorites = saved.get("favorites", [])
            if isinstance(favorites, list):
                settings["favorites"] = [str(item) for item in favorites]
    except Exception:
        pass
    if not settings["language"]:
        settings["language"] = detect_system_language()
    return settings

def save_app_settings(root: Path, settings: Dict) -> None:
    path = settings_path(root)
    try:
        path.parent.mkdir(exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(settings, file, ensure_ascii=False)
    except OSError:
        pass

def load_language_preference(root: Path) -> str:
    return load_app_settings(root)["language"]

def save_language_preference(root: Path, lang: str) -> None:
    settings = load_app_settings(root)
    settings["language"] = lang
    save_app_settings(root, settings)

def validate_launch(root: Path) -> bool:
    root_name = root.name.lower()
    exe_name = Path(sys.argv[0]).stem.lower()
    name_ok = any(part in root_name for part in ALLOWED_NAME_PARTS) or any(
        part in exe_name for part in ALLOWED_NAME_PARTS
    )
    if not name_ok:
        box = QMessageBox()
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(tr("launch_blocked_title"))
        box.setText(tr("launch_blocked_name_text"))
        box.exec()
        return False

    if is_temporary_location(root) or is_temporary_location(Path(sys.argv[0]).resolve().parent):
        box = QMessageBox()
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(tr("launch_blocked_title"))
        box.setText(tr("launch_blocked_temp_text"))
        box.exec()
        return False

    return True

def load_program_data(root: Path) -> Dict[str, List[Dict]]:
    data_path = root / DATA_FILE
    try:
        with open(data_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as exc:
        QMessageBox.warning(
            None,
            tr("catalog_missing_title"),
            tr("catalog_missing_text", error=exc),
        )
        return {"programs": [], "categories": [], "whitelist": []}

    data.setdefault("programs", [])
    data.setdefault("categories", [])
    data.setdefault("whitelist", [])
    return data

def get_download_folder() -> Path:
    home = Path.home()
    downloads = home / "Downloads"
    downloads.mkdir(exist_ok=True)
    return downloads

def format_bytes(size: int) -> str:
    if size <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    power = int(math.log(size, 1024))
    power = max(0, min(power, len(units) - 1))
    value = size / math.pow(1024, power)
    return f"{value:.1f} {units[power]}"

_ILLEGAL_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')

def sanitize_filename(name: str) -> str:
    # Servers sometimes send filenames with characters Windows paths can't
    # contain (or mangled encodings) — strip/replace them instead of crashing
    # the download with an "Invalid argument" OS error.
    name = (name or "").strip()
    name = _ILLEGAL_FILENAME_CHARS.sub("_", name)
    name = name.strip(" .")
    if len(name) > 180:
        stem = Path(name).stem[:150]
        suffix = Path(name).suffix[:20]
        name = stem + suffix
    return name

def accent_for(name: str) -> QColor:
    index = sum(ord(ch) for ch in name) % len(ACCENT_PALETTE)
    return QColor(ACCENT_PALETTE[index])

def create_icon(name: str, color: QColor, letters: Optional[str] = None) -> QIcon:
    cache_key = f"{name}_{color.name()}_{letters}"
    if cache_key in ICON_CACHE:
        return ICON_CACHE[cache_key]

    size = 72
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    
    gradient = QtGui.QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, color.lighter(130))
    gradient.setColorAt(1.0, color.darker(120))
    
    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, size, size, 20, 20)
    
    painter.setPen(QtGui.QPen(Qt.GlobalColor.white))
    label = letters if letters else (name[0].upper() if name else "?")
    font_size = 26 if len(label) <= 1 else 18
    font = QFont("Segoe UI", font_size, QFont.Weight.Black)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, label)
    painter.end()
    
    icon = QIcon(pixmap)
    ICON_CACHE[cache_key] = icon
    return icon

GLOW_CACHE: Dict[str, QPixmap] = {}

def create_glow_pixmap(color: QColor, size: int = 96) -> QPixmap:
    # A precomputed soft radial gradient. Pulsing this via opacity is far cheaper
    # than animating a QGraphicsDropShadowEffect's blurRadius, which forces a full
    # Gaussian re-blur on every single animation frame.
    cache_key = f"{color.name()}_{size}"
    if cache_key in GLOW_CACHE:
        return GLOW_CACHE[cache_key]

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    gradient = QRadialGradient(size / 2, size / 2, size / 2)
    glow_color = QColor(color)
    glow_color.setAlpha(200)
    gradient.setColorAt(0.0, glow_color)
    mid_color = QColor(color)
    mid_color.setAlpha(60)
    gradient.setColorAt(0.55, mid_color)
    edge_color = QColor(color)
    edge_color.setAlpha(0)
    gradient.setColorAt(1.0, edge_color)
    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    painter.end()

    GLOW_CACHE[cache_key] = pixmap
    return pixmap

def create_search_icon(color: str = "#8B93AA") -> QIcon:
    size = 32
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QtGui.QPen(QColor(color))
    pen.setWidthF(2.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QtCore.QRectF(6, 6, 14, 14))
    painter.drawLine(QtCore.QPointF(21, 21), QtCore.QPointF(27, 27))
    painter.end()
    return QIcon(pixmap)

class DownloadWorker(QtCore.QThread):
    progress_changed = QtCore.pyqtSignal(int, float)
    finished = QtCore.pyqtSignal(Path)
    error = QtCore.pyqtSignal(str)

    def __init__(self, url: str, base_dest: Path):
        super().__init__()
        self.url = url
        self.base_dest = base_dest

    def _parse_filename(self, response: requests.Response) -> str:
        def decode_rfc2047(value: str) -> str:
            # Some servers still send filename="=?UTF-8?Q?...?=" (RFC 2047) instead
            # of the modern filename*=UTF-8''... form. Decode it if present.
            if "=?" in value and "?=" in value:
                try:
                    from email.header import decode_header
                    decoded_parts = decode_header(value)
                    pieces = []
                    for text, encoding in decoded_parts:
                        if isinstance(text, bytes):
                            pieces.append(text.decode(encoding or "utf-8", errors="replace"))
                        else:
                            pieces.append(text)
                    return "".join(pieces)
                except Exception:
                    return value
            return value

        def parse_disposition(disposition_value: str) -> Optional[str]:
            parts = [part.strip() for part in disposition_value.split(";") if part.strip()]
            filename = None
            for part in parts:
                if part.lower().startswith("filename*="):
                    _, value = part.split("=", 1)
                    if value.startswith("UTF-8''"):
                        value = value[7:]
                    filename = unquote(value.strip('"'))
                    break
                if part.lower().startswith("filename="):
                    _, value = part.split("=", 1)
                    filename = decode_rfc2047(value.strip('"'))
                    break
            return filename

        disposition = response.headers.get("content-disposition", "")
        if disposition:
            filename = parse_disposition(disposition)
            if filename:
                safe = sanitize_filename(Path(filename).name)
                if safe:
                    return safe

        parsed = urlparse(response.url)
        candidate = sanitize_filename(Path(parsed.path).name)
        if candidate and Path(candidate).suffix:
            return candidate

        content_type = response.headers.get("content-type", "").lower()
        if "zip" in content_type:
            return self.base_dest.name + ".zip"
        if "exe" in content_type or "application/octet-stream" in content_type or "msdos-program" in content_type:
            return self.base_dest.name + ".exe"
        return self.base_dest.name + ".bin"

    def run(self) -> None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
            )
        }
        temp_name = None
        try:
            with requests.get(
                self.url, stream=True, timeout=20, headers=headers, allow_redirects=True, verify=True
            ) as response:
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if content_type.startswith("text/html"):
                    raise RuntimeError(tr("html_response_error"))

                file_name = self._parse_filename(response)
                dest = self.base_dest.parent / file_name
                temp_name = dest.parent / (dest.name + ".part")
                total_length = int(response.headers.get("content-length", 0) or 0)
                downloaded = 0
                start_time = time.perf_counter()
                with open(temp_name, "wb") as output:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            output.write(chunk)
                            downloaded += len(chunk)
                            elapsed = max(time.perf_counter() - start_time, 0.001)
                            speed = downloaded / elapsed
                            percent = int(downloaded / total_length * 100) if total_length else 0
                            self.progress_changed.emit(percent, speed)
                temp_name.replace(dest)
                self.finished.emit(dest)
        except Exception as exc:
            if temp_name is not None and temp_name.exists():
                try:
                    temp_name.unlink()
                except OSError:
                    pass
            self.error.emit(str(exc))

class ProgramCard(QWidget):
    favorite_toggled = QtCore.pyqtSignal(str, bool)

    def __init__(
        self,
        program: Dict,
        category_name: str,
        performance_mode: bool = False,
        is_favorite: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.program = program
        self.performance_mode = performance_mode
        self.is_favorite = is_favorite
        self.setObjectName("ProgramCard")
        self.setFixedHeight(164)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._active_shadow_anim = None
        self._entrance_anim = None
        self._entrance_timer = None
        self._hover_anim: Optional[QPropertyAnimation] = None
        self._alive = True

        accent = program.get("accent")
        self.accent_color = QColor(accent) if accent else accent_for(program["name"])

        self.shadow: Optional[QGraphicsDropShadowEffect] = None
        if not self.performance_mode:
            self._install_shadow()
        self.setStyleSheet(self.card_style(normal=True))

        self.icon_label = QLabel()
        self.icon_label.setPixmap(create_icon(program["name"], self.accent_color).pixmap(76, 76))
        self.icon_label.setFixedSize(88, 88)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet(
            f"background: rgba({self.accent_color.red()}, {self.accent_color.green()}, {self.accent_color.blue()}, 0.14);"
            " border-radius: 24px;"
        )

        self.title_label = QLabel(program["name"])
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setStyleSheet("font-size: 15.5pt; font-weight: 800; color: #FAFAFF; letter-spacing: -0.2px;")

        category_icon = CATEGORY_ICONS.get(program.get("category", ""), DEFAULT_CATEGORY_ICON)
        self.category_label = QLabel(f"{category_icon}  {category_name}")
        self.category_label.setStyleSheet(
            f"color: {self.accent_color.lighter(145).name()}; font-size: 8.3pt; font-weight: 700;"
            f" background: rgba({self.accent_color.red()}, {self.accent_color.green()}, {self.accent_color.blue()}, 0.16);"
            " border: none; border-radius: 8px; padding: 4px 11px;"
        )

        description = localized(program.get("description", ""), tr.lang)
        self.description_label = QLabel(description)
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #9199B0; font-size: 9.7pt; line-height: 1.35; font-weight: 500;")

        self.size_label = QLabel(f"📦 {program.get('size', '—')}")
        self.size_label.setStyleSheet("color: #6B7280; font-size: 9pt; font-weight: 700;")

        self.download_button = QPushButton(f"⬇  {tr('download_button')}")
        self.download_button.setObjectName("DownloadButton")
        self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_button.setFixedSize(144, 44)

        self.favorite_button = QPushButton()
        self.favorite_button.setObjectName("FavoriteButton")
        self.favorite_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.favorite_button.setFixedSize(34, 34)
        self.favorite_button.setToolTip(tr("favorite_tooltip"))
        self.favorite_button.clicked.connect(self._toggle_favorite)
        self._refresh_favorite_style()

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(self.title_label, stretch=1)
        title_row.addWidget(self.favorite_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(7)
        text_layout.addLayout(title_row)
        text_layout.addWidget(self.category_label, alignment=Qt.AlignmentFlag.AlignLeft)
        text_layout.addWidget(self.description_label)
        text_layout.addStretch(1)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        right_layout.addWidget(self.size_label, alignment=Qt.AlignmentFlag.AlignRight)
        right_layout.addStretch(1)
        right_layout.addWidget(self.download_button, alignment=Qt.AlignmentFlag.AlignRight)

        accent_bar = QLabel()
        accent_bar.setObjectName("AccentBar")
        accent_bar.setFixedWidth(4)
        accent_bar.setStyleSheet(
            f"background: rgba({self.accent_color.red()}, {self.accent_color.green()}, {self.accent_color.blue()}, 0.55);"
            " border-radius: 2px;"
        )
        self.accent_bar = accent_bar

        card_layout = QHBoxLayout(self)
        card_layout.addWidget(accent_bar)
        card_layout.addSpacing(14)
        card_layout.addWidget(self.icon_label)
        card_layout.addSpacing(18)
        card_layout.addLayout(text_layout, stretch=1)
        card_layout.addLayout(right_layout)
        card_layout.setContentsMargins(16, 20, 24, 20)

    def closeEvent(self, event):
        self.cancel_pending()
        super().closeEvent(event)

    def cancel_pending(self) -> None:
        # Stops any in-flight timers/animations before the widget is torn down,
        # so a delayed callback can never fire against an already-deleted card.
        self._alive = False
        try:
            if self._active_shadow_anim and self._active_shadow_anim.state() == QPropertyAnimation.State.Running:
                self._active_shadow_anim.stop()
            if self._entrance_anim and self._entrance_anim.state() == QPropertyAnimation.State.Running:
                self._entrance_anim.stop()
            if self._hover_anim and self._hover_anim.state() == QPropertyAnimation.State.Running:
                self._hover_anim.stop()
            if self._entrance_timer and self._entrance_timer.isActive():
                self._entrance_timer.stop()
        except RuntimeError:
            pass

    def _toggle_favorite(self) -> None:
        self.is_favorite = not self.is_favorite
        self._refresh_favorite_style()
        self.favorite_toggled.emit(self.program.get("name", ""), self.is_favorite)

    def _refresh_favorite_style(self) -> None:
        star = "★" if self.is_favorite else "☆"
        color = "#FFD700" if self.is_favorite else "#8B93AA"
        self.favorite_button.setText(star)
        self.favorite_button.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {color}; font-size: 16pt; }}"
            f" QPushButton:hover {{ color: #FFD700; }}"
        )

    def _install_shadow(self, blur_radius: float = 20.0, glow: bool = False) -> None:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur_radius)
        if glow:
            shadow.setOffset(0, 6)
            shadow.setColor(QColor(self.accent_color.red(), self.accent_color.green(), self.accent_color.blue(), 130))
        else:
            shadow.setOffset(0, 6)
            shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)
        self.shadow = shadow

    def _animate_shadow_to(self, target_blur: float, glow: bool = False) -> None:
        if self.shadow is None:
            return

        target_color = (
            QColor(self.accent_color.red(), self.accent_color.green(), self.accent_color.blue(), 130)
            if glow else QColor(0, 0, 0, 120)
        )
        self.shadow.setColor(target_color)

        if self._active_shadow_anim and self._active_shadow_anim.state() == QPropertyAnimation.State.Running:
            self._active_shadow_anim.stop()

        anim = QPropertyAnimation(self.shadow, b"blurRadius", self)
        anim.setDuration(260)
        anim.setEasingCurve(QEasingCurve.Type.OutExpo)
        anim.setStartValue(self.shadow.blurRadius())
        anim.setEndValue(target_blur)
        self._active_shadow_anim = anim
        anim.start()

    def play_entrance_animation(self, delay_ms: int = 0) -> None:
        if self.performance_mode:
            # Skip the fade + shadow-rebuild churn entirely in performance mode.
            self.setGraphicsEffect(None)
            return

        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0.0)
        self.setGraphicsEffect(effect)
        self.shadow = None

        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def rebuild_shadow():
            if self._alive and not self.isHidden():
                self._install_shadow(blur_radius=20.0)

        anim.finished.connect(rebuild_shadow)
        self._entrance_anim = anim

        if delay_ms > 0:
            self._entrance_timer = QTimer(self)
            self._entrance_timer.setSingleShot(True)
            self._entrance_timer.timeout.connect(self._start_entrance_anim)
            self._entrance_timer.start(delay_ms)
        else:
            anim.start()

    def _start_entrance_anim(self) -> None:
        if self._alive and self._entrance_anim is not None:
            self._entrance_anim.start()

    def card_style(self, normal: bool = True) -> str:
        a = self.accent_color
        if normal:
            bg = "rgba(255, 255, 255, 0.045)"
            border = "1px solid rgba(255, 255, 255, 0.07)"
        else:
            bg = "rgba(255, 255, 255, 0.075)"
            border = f"1.5px solid rgba({a.red()}, {a.green()}, {a.blue()}, 0.45)"
        return (
            f"QWidget#ProgramCard {{"
            f" background: {bg};"
            f" border: {border};"
            f" border-radius: 24px;"
            f"}}"
        )

    def enterEvent(self, event: QtCore.QEvent) -> None:
        self.setStyleSheet(self.card_style(normal=False))
        self._animate_shadow_to(34, glow=True)
        self._animate_icon_pop(True)
        a = self.accent_color
        self.accent_bar.setStyleSheet(f"background: rgba({a.red()}, {a.green()}, {a.blue()}, 0.95); border-radius: 2px;")
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self.setStyleSheet(self.card_style(normal=True))
        self._animate_shadow_to(20, glow=False)
        self._animate_icon_pop(False)
        a = self.accent_color
        self.accent_bar.setStyleSheet(f"background: rgba({a.red()}, {a.green()}, {a.blue()}, 0.55); border-radius: 2px;")
        super().leaveEvent(event)

    def _animate_icon_pop(self, grow: bool) -> None:
        # Мягкое "увеличение" иконки при наведении — безопасно для QVBoxLayout,
        # т.к. контейнер иконки имеет фиксированный размер, меняется только сам pixmap.
        if self._hover_anim and self._hover_anim.state() == QPropertyAnimation.State.Running:
            self._hover_anim.stop()

        target_size = 82 if grow else 76
        self.icon_label.setPixmap(
            create_icon(self.program["name"], self.accent_color).pixmap(target_size, target_size)
        )

class SettingsDialog(QDialog):
    settings_changed = QtCore.pyqtSignal()

    def __init__(self, root: Path, settings: Dict, parent=None):
        super().__init__(parent)
        self.root = root
        self.settings = settings
        self.setWindowTitle(tr("settings_title"))
        self.setFixedSize(420, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QWidget()
        self.container.setStyleSheet(
            "* { outline: none; font-family: 'Segoe UI Variable', 'Segoe UI', system-ui, sans-serif; }"
            "QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(20,16,38,0.97), stop:1 rgba(12,12,22,0.97));"
            " border: 1px solid rgba(255, 255, 255, 0.09); border-radius: 24px; }"
            "QLabel { color: white; font-weight: 700; font-size: 11pt; border: none; background: transparent; }"
            "QPushButton { background: rgba(255,255,255,0.06); color: white; border-radius: 14px; padding: 10px;"
            " border: 1px solid rgba(255,255,255,0.07); font-weight: 600; }"
            "QPushButton:hover { background: rgba(0, 224, 255, 0.15); color: #6FF3FF; border: 1px solid rgba(0,224,255,0.35); }"
        )
        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(50)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 170))
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(26, 26, 26, 26)
        container_layout.setSpacing(10)
        
        self.path_label = QLabel(tr("download_folder_lbl"))
        self.path_value = QLabel(str(get_download_folder()))
        self.path_value.setStyleSheet("color: #9CA3AF; font-size: 9pt; font-weight: 500;")
        
        change_path_btn = QPushButton(tr("change_folder_btn"))
        change_path_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_path_btn.clicked.connect(self.change_folder)

        container_layout.addWidget(self.path_label)
        container_layout.addWidget(self.path_value)
        container_layout.addWidget(change_path_btn)
        container_layout.addSpacing(6)

        self.performance_toggle = self._build_toggle_row(
            container_layout,
            tr("performance_mode_lbl"),
            tr("performance_mode_hint"),
            "performance_mode",
        )
        self.always_on_top_toggle = self._build_toggle_row(
            container_layout,
            tr("always_on_top_lbl"),
            None,
            "always_on_top",
        )

        hint_label = QLabel(tr("settings_restart_hint"))
        hint_label.setStyleSheet("color: #565D74; font-size: 8.5pt; font-weight: 600;")
        container_layout.addWidget(hint_label)

        close_btn = QPushButton(tr("close_btn"))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7A17FF, stop:1 #00E0FF);"
            " font-weight: 800; color: white; border: none; border-radius: 14px;"
        )
        close_btn.clicked.connect(self.accept)
        
        container_layout.addStretch(1)
        container_layout.addWidget(close_btn)
        
        self.layout.addWidget(self.container)

    def _build_toggle_row(self, layout: QVBoxLayout, label_text: str, hint_text: Optional[str], key: str) -> QPushButton:
        row = QHBoxLayout()
        row.setSpacing(10)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        row_label = QLabel(label_text)
        row_label.setStyleSheet("font-size: 10pt; font-weight: 700;")
        text_box.addWidget(row_label)
        if hint_text:
            hint = QLabel(hint_text)
            hint.setWordWrap(True)
            hint.setStyleSheet("color: #8B93AA; font-size: 8pt; font-weight: 500;")
            text_box.addWidget(hint)

        toggle_btn = QPushButton()
        toggle_btn.setFixedSize(72, 32)
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        def refresh():
            enabled = bool(self.settings.get(key, False))
            toggle_btn.setText(tr("on_lbl") if enabled else tr("off_lbl"))
            if enabled:
                toggle_btn.setStyleSheet(
                    "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7A17FF, stop:1 #00E0FF);"
                    " color: white; font-weight: 800; border: none; border-radius: 14px;"
                )
            else:
                toggle_btn.setStyleSheet(
                    "background: rgba(255,255,255,0.06); color: #9CA3AF; font-weight: 700;"
                    " border: 1px solid rgba(255,255,255,0.09); border-radius: 14px;"
                )

        def on_click():
            self.settings[key] = not bool(self.settings.get(key, False))
            save_app_settings(self.root, self.settings)
            refresh()
            self.settings_changed.emit()

        toggle_btn.clicked.connect(on_click)
        refresh()

        row.addLayout(text_box, stretch=1)
        row.addWidget(toggle_btn, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(row)
        return toggle_btn

    def change_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr("select_folder_dialog"))
        if folder:
            self.path_value.setText(folder)

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setStyleSheet("* { outline: none; } background: transparent;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setPixmap(get_brand_pixmap(TITLE_BAR_ICON_SIZE))
        icon_label.setFixedSize(TITLE_BAR_ICON_SIZE, TITLE_BAR_ICON_SIZE)
        icon_label.setScaledContents(True)

        title = QLabel(APP_NAME)
        title.setStyleSheet("color: #6B7280; font-weight: 700; font-size: 9.5pt; letter-spacing: 0.5px; border: none;")
        
        btn_style = (
            "QPushButton { background: transparent; border: none; color: #8B93AA; font-size: 11pt; font-weight: bold; border-radius: 9px; }"
            "QPushButton:hover { color: white; background: rgba(255,255,255,0.09); }"
        )
        
        self.min_btn = QPushButton("—")
        self.min_btn.setFixedSize(30, 30)
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.setStyleSheet(btn_style)
        self.min_btn.clicked.connect(self.parent.showMinimized)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet(btn_style + "QPushButton:hover { color: white; background: #FF3366; }")
        self.close_btn.clicked.connect(self.parent.close)
        
        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(self.min_btn)
        layout.addWidget(self.close_btn)
        
        self._start_pos = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._start_pos is not None:
            delta = event.globalPosition().toPoint() - self._start_pos
            self.parent.move(self.parent.pos() + delta)
            self._start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._start_pos = None

class MainWindow(QMainWindow):
    def __init__(self, root: Path, data: Dict[str, List[Dict]]):
        super().__init__()
        self.root = root
        self.data = data
        self.programs = data.get("programs", [])
        self.categories = data.get("categories", [])
        self.whitelist = set(data.get("whitelist", []))
        self.download_folder = get_download_folder()
        self.active_category = "all"
        self.download_thread: Optional[DownloadWorker] = None
        self.download_in_progress = False
        self.central: Optional[QWidget] = None
        self.language_buttons: List[QPushButton] = []

        self.app_settings = load_app_settings(root)
        self.favorites = set(self.app_settings.get("favorites", []))
        self.performance_mode = bool(self.app_settings.get("performance_mode", False))

        # Debounce search-as-you-type so cards aren't rebuilt on every keystroke.
        self._search_debounce = QTimer(self)
        self._search_debounce.setSingleShot(True)
        self._search_debounce.timeout.connect(lambda: self.load_cards(animate=False))

        # Reveal cards on a single shared timer instead of one QTimer per card.
        self._reveal_queue: List["ProgramCard"] = []
        self._reveal_timer = QTimer(self)
        self._reveal_timer.setInterval(35)
        self._reveal_timer.timeout.connect(self._reveal_next_card)

        flags = Qt.WindowType.FramelessWindowHint
        if self.app_settings.get("always_on_top"):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1180, 750)

        self.rebuild_ui()

    def app_stylesheet(self) -> str:
        # Glassmorphism / premium theme — Steam x Discord x Fluent x macOS vibe
        return (
            "* { outline: none; font-family: 'Segoe UI Variable', 'Segoe UI', system-ui, sans-serif; }"
            "QMainWindow { background-color: transparent; }"

            "QWidget#AppHeader {"
            " background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            " stop:0 rgba(24, 14, 56, 0.85), stop:0.45 rgba(30, 18, 70, 0.85),"
            " stop:1 rgba(12, 18, 38, 0.85));"
            " border-radius: 26px; border: 1px solid rgba(255,255,255,0.09); }"

            "QWidget#Sidebar {"
            " background: rgba(20, 18, 34, 0.55);"
            " border: 1px solid rgba(255,255,255,0.07); border-radius: 26px; }"

            "QScrollArea { background: transparent; border: none; }"
            "QWidget#CardsContainer { background: transparent; }"
            "QScrollBar:vertical { background: transparent; width: 9px; margin: 2px; }"
            "QScrollBar::handle:vertical { background: rgba(255,255,255,0.16); border-radius: 4px; min-height: 40px; border: none; }"
            "QScrollBar::handle:vertical:hover { background: rgba(0, 224, 255, 0.55); }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"

            "QLineEdit {"
            " background: rgba(255,255,255,0.05); border: 1.5px solid rgba(255,255,255,0.09);"
            " border-radius: 16px; color: #F5F5FA; padding: 13px 14px 13px 42px; font-size: 10.5pt; font-weight: 500; }"
            "QLineEdit:hover { background: rgba(255,255,255,0.075); border: 1.5px solid rgba(255,255,255,0.16); }"
            "QLineEdit:focus { background: rgba(255,255,255,0.08); border: 1.5px solid rgba(0, 224, 255, 0.55); }"

            "QPushButton#CategoryButton {"
            " background: transparent; color: #9CA3AF; border: none; border-left: 3px solid transparent; font-size: 10.8pt;"
            " padding: 13px 16px; text-align: left; font-weight: 600; border-radius: 15px; }"
            "QPushButton#CategoryButton:hover {"
            " color: #FFFFFF; background: rgba(255,255,255,0.055); border-left: 3px solid rgba(255,255,255,0.18); }"
            "QPushButton#CategoryActive {"
            " color: #E8FBFF; font-weight: 800;"
            " background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0,224,255,0.22), stop:1 rgba(112,0,255,0.16));"
            " border: none; border-left: 3px solid #00E0FF; border-radius: 15px; padding: 13px 16px;"
            " text-align: left; font-size: 10.8pt; }"

            "QPushButton#DownloadButton {"
            " background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7A17FF, stop:1 #00E0FF);"
            " color: white; border: 1.5px solid rgba(255,255,255,0.25); border-radius: 21px; font-size: 10pt; font-weight: 800;"
            " letter-spacing: 0.3px; }"
            "QPushButton#DownloadButton:hover {"
            " background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9640FF, stop:1 #4FF0FF);"
            " border: 1.5px solid rgba(255,255,255,0.55); }"
            "QPushButton#DownloadButton:pressed { background: #5B00CC; border: 1.5px solid rgba(255,255,255,0.2); }"

            "QPushButton#AboutButton {"
            " background: rgba(255,255,255,0.055); color: #E5E7EB; border: 1px solid rgba(255,255,255,0.08);"
            " border-radius: 16px; font-weight: 700; font-size: 9.5pt; }"
            "QPushButton#AboutButton:hover {"
            " background: rgba(0, 224, 255, 0.12); color: #6FF3FF; border: 1px solid rgba(0,224,255,0.3); }"

            "QPushButton#LangButton {"
            " background: rgba(255,255,255,0.03); color: #7B8296; border: 1px solid transparent;"
            " border-radius: 10px; font-size: 9pt; font-weight: 700; padding: 6px; }"
            "QPushButton#LangButton:hover { color: #FFFFFF; background: rgba(255,255,255,0.08); }"
            "QPushButton#LangButtonActive {"
            " background: rgba(0, 224, 255, 0.18); color: #6FF3FF; border: 1px solid rgba(0,224,255,0.4);"
            " border-radius: 10px; font-size: 9pt; font-weight: 900; padding: 6px; }"

            "QLabel#HeaderTitle {"
            " font-size: 27pt; font-weight: 900; color: #FFFFFF; letter-spacing: -0.8px; }"
            "QLabel#HeaderSubtitle { color: #A7ADC2; font-size: 10.8pt; font-weight: 500; }"
            "QLabel#HeaderInfo { color: #6FF3FF; font-size: 10pt; font-weight: 700; }"
            "QLabel#EmptyState { color: #565D74; font-size: 14pt; font-weight: 700; }"
        )

    def rebuild_ui(self) -> None:
        old_percent = self.progress_bar.value() if hasattr(self, "progress_bar") else 0
        old_search_text = self.search_input.text() if hasattr(self, "search_input") else ""

        if self.central is not None:
            self.central.deleteLater()

        self.central = QWidget()
        self.central.setObjectName("AppBackground")
        self.setStyleSheet(self.app_stylesheet())

        main_layout = QVBoxLayout(self.central)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        content_container = QWidget()
        content_container.setObjectName("GlassRoot")
        content_container.setStyleSheet(
            "QWidget#GlassRoot {"
            " background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            " stop:0 rgba(13, 10, 26, 0.97), stop:0.5 rgba(9, 9, 20, 0.97), stop:1 rgba(15, 11, 28, 0.97));"
            " border-radius: 26px; border: 1px solid rgba(255, 255, 255, 0.07); }"
        )
        if not self.performance_mode:
            outer_glow = QGraphicsDropShadowEffect(content_container)
            outer_glow.setBlurRadius(60)
            outer_glow.setOffset(0, 12)
            outer_glow.setColor(QColor(0, 0, 0, 160))
            content_container.setGraphicsEffect(outer_glow)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(16, 0, 16, 16)

        self.title_bar = CustomTitleBar(self)
        content_layout.addWidget(self.title_bar)

        content_layout.addWidget(self.build_header())
        content_layout.addWidget(self._build_divider())
        content_layout.addLayout(self.build_main_area())
        content_layout.addWidget(self.build_status_bar())

        main_layout.addWidget(content_container)
        self.setCentralWidget(self.central)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(old_percent)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: rgba(255,255,255,0.05); color: #FFFFFF; border: 1px solid rgba(255,255,255,0.07);"
            " border-radius: 11px; font-size: 9.5pt; font-weight: 800; text-align: center; }"
            "QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7A17FF, stop:0.55 #B026FF, stop:1 #00E0FF);"
            " border-radius: 11px; border: none; margin: 1px; }"
        )
        if not self.performance_mode:
            progress_glow = QGraphicsDropShadowEffect(self.progress_bar)
            progress_glow.setBlurRadius(22)
            progress_glow.setOffset(0, 0)
            progress_glow.setColor(QColor(0, 224, 255, 110))
            self.progress_bar.setGraphicsEffect(progress_glow)
        self.status_bar_layout.addWidget(self.progress_bar, stretch=1)
        
        if self.download_in_progress:
            self.set_download_status(tr("downloading_status", name=""))
        else:
            self.status_text.setText(tr("status_copyright", brand=BRANDING))

        for button, button_id in zip(self.category_buttons, self.category_ids):
            button.setObjectName("CategoryActive" if button_id == self.active_category else "CategoryButton")
            button.style().unpolish(button)
            button.style().polish(button)

        if old_search_text:
            self.search_input.setText(old_search_text) 
        else:
            self.load_cards()

        self._highlight_active_language()

    def build_header(self) -> QWidget:
        header_widget = QWidget()
        header_widget.setObjectName("AppHeader")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(32, 24, 32, 24)
        header_layout.setSpacing(24)

        logo_stack = QWidget()
        logo_stack.setFixedSize(126, 126)

        if not self.performance_mode:
            glow_label = QLabel(logo_stack)
            glow_label.setGeometry(0, 0, 126, 126)
            glow_label.setPixmap(create_glow_pixmap(QColor("#00E0FF"), 126))
            glow_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            glow_opacity = QGraphicsOpacityEffect(glow_label)
            glow_opacity.setOpacity(0.45)
            glow_label.setGraphicsEffect(glow_opacity)

            logo_anim = QPropertyAnimation(glow_opacity, b"opacity", logo_stack)
            logo_anim.setDuration(1800)
            logo_anim.setStartValue(0.3)
            logo_anim.setEndValue(0.85)
            logo_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
            self._logo_glow_anim = logo_anim

            def _bounce_logo_glow():
                if logo_anim.direction() == QPropertyAnimation.Direction.Forward:
                    logo_anim.setDirection(QPropertyAnimation.Direction.Backward)
                else:
                    logo_anim.setDirection(QPropertyAnimation.Direction.Forward)
                logo_anim.start()

            logo_anim.finished.connect(_bounce_logo_glow)
            logo_anim.start()

        logo_label = QLabel(logo_stack)
        logo_label.setGeometry(12, 12, 102, 102)
        logo_label.setPixmap(get_brand_pixmap(102))

        title_label = QLabel(APP_NAME)
        title_label.setObjectName("HeaderTitle")
        
        subtitle_label = QLabel(tr("app_subtitle", brand=BRANDING))
        subtitle_label.setObjectName("HeaderSubtitle")

        self.stats_label = QLabel()
        self.stats_label.setObjectName("HeaderInfo")
        self.update_stats_label()

        title_box = QVBoxLayout()
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        title_box.addSpacing(6)
        title_box.addWidget(self.stats_label)

        header_layout.addWidget(logo_stack, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addLayout(title_box)
        header_layout.addStretch(1)

        controls_box = QVBoxLayout()
        controls_box.setSpacing(12)

        contact_label = QLabel(f"✉  {CONTACT_EMAIL}")
        contact_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        contact_label.setStyleSheet(
            "color: #6FF3FF; font-size: 11pt; font-weight: 700; letter-spacing: 0.2px;"
            " background: rgba(0, 224, 255, 0.08); border: 1px solid rgba(0, 224, 255, 0.22);"
            " border-radius: 12px; padding: 7px 14px;"
        )
        contact_label.setCursor(Qt.CursorShape.PointingHandCursor)
        contact_label.setToolTip(CONTACT_EMAIL)
        controls_box.addWidget(contact_label, alignment=Qt.AlignmentFlag.AlignRight)

        controls_box.addWidget(self.build_language_switcher(), alignment=Qt.AlignmentFlag.AlignRight)

        btn_layout = QHBoxLayout()
        
        settings_button = QPushButton(f"⚙️ {tr('settings_btn')}")
        settings_button.setObjectName("AboutButton")
        settings_button.setFixedSize(130, 36)
        settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_button.clicked.connect(self.show_settings_dialog)
        
        about_button = QPushButton(f"ℹ️ {tr('about_button')}")
        about_button.setObjectName("AboutButton")
        about_button.setFixedSize(130, 36)
        about_button.setCursor(Qt.CursorShape.PointingHandCursor)
        about_button.clicked.connect(self.show_about_dialog)

        btn_layout.addWidget(settings_button)
        btn_layout.addWidget(about_button)
        
        controls_box.addLayout(btn_layout)
        header_layout.addLayout(controls_box)
        
        return header_widget

    def _build_divider(self) -> QWidget:
        divider = QWidget()
        divider.setFixedHeight(2)
        divider.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            " stop:0 rgba(122,23,255,0), stop:0.5 rgba(0,224,255,0.45), stop:1 rgba(122,23,255,0));"
        )
        return divider

    def show_settings_dialog(self):
        dialog = SettingsDialog(self.root, self.app_settings, self)
        dialog.settings_changed.connect(self.apply_settings_change)
        dialog.exec()

    def apply_settings_change(self) -> None:
        new_performance_mode = bool(self.app_settings.get("performance_mode", False))
        performance_changed = new_performance_mode != self.performance_mode
        self.performance_mode = new_performance_mode

        flags = Qt.WindowType.FramelessWindowHint
        if self.app_settings.get("always_on_top"):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        if was_visible:
            self.show()

        if performance_changed:
            self.rebuild_ui()

    def build_language_switcher(self) -> QWidget:
        switcher = QWidget()
        switcher.setToolTip(tr("language_tooltip"))
        layout = QHBoxLayout(switcher)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.language_buttons = []
        for code in LANGUAGES:
            button = QPushButton(f"{LANGUAGE_FLAGS[code]} {LANGUAGE_LABELS[code]}")
            button.setObjectName("LangButtonActive" if code == tr.lang else "LangButton")
            button.setFixedSize(70, 32)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked, lang_code=code: self.apply_language(lang_code))
            self.language_buttons.append((button, code))
            layout.addWidget(button)

        return switcher

    def _highlight_active_language(self) -> None:
        for button, code in self.language_buttons:
            button.setObjectName("LangButtonActive" if code == tr.lang else "LangButton")
            button.style().unpolish(button)
            button.style().polish(button)

    def apply_language(self, lang: str) -> None:
        if lang == tr.lang:
            return
        tr.set_language(lang)
        save_language_preference(self.root, lang)
        self.rebuild_ui()

    def update_stats_label(self) -> None:
        self.stats_label.setText(tr("stats", count=len(self.programs), cats=len(self.categories)))

    def category_display_name(self, category_id: str) -> str:
        if category_id == FAVORITES_CATEGORY_ID:
            return tr("favorites_category")
        for category in self.categories:
            if category["id"] == category_id:
                return localized(category.get("name", category_id), tr.lang)
        return category_id

    def build_main_area(self) -> QHBoxLayout:
        area_layout = QHBoxLayout()
        area_layout.setSpacing(20)

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(24, 24, 24, 24)
        sidebar_layout.setSpacing(12)

        search_input = QLineEdit()
        placeholder_text = tr("search_placeholder").replace("🔍", "").strip()
        search_input.setPlaceholderText(placeholder_text)
        search_input.addAction(create_search_icon(), QLineEdit.ActionPosition.LeadingPosition)
        search_input.setFixedHeight(46)
        search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input = search_input
        sidebar_layout.addWidget(search_input)
        sidebar_layout.addSpacing(10)

        categories_label = QLabel(tr("categories_label"))
        categories_label.setStyleSheet(
            "color: #626A80; font-size: 9pt; font-weight: 800; letter-spacing: 1.6px; padding: 4px 6px 2px 6px;"
        )
        sidebar_layout.addWidget(categories_label)

        self.category_buttons: List[QPushButton] = []
        self.category_ids: List[str] = ["all"]

        all_icon = CATEGORY_ICONS["all"]
        all_button = QPushButton(f"{all_icon}  {tr('all_programs')}   ·  {len(self.programs)}")
        all_button.setObjectName("CategoryButton")
        all_button.setCursor(Qt.CursorShape.PointingHandCursor)
        all_button.clicked.connect(lambda: self.set_category("all"))
        self.category_buttons.append(all_button)
        sidebar_layout.addWidget(all_button)

        for category in self.categories:
            icon = CATEGORY_ICONS.get(category["id"], DEFAULT_CATEGORY_ICON)
            name = localized(category.get("name", category["id"]), tr.lang)
            count = sum(1 for p in self.programs if p.get("category") == category["id"])
            button = QPushButton(f"{icon}  {name}   ·  {count}")
            button.setObjectName("CategoryButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked, code=category["id"]: self.set_category(code))
            self.category_buttons.append(button)
            self.category_ids.append(category["id"])
            sidebar_layout.addWidget(button)

        favorites_button = QPushButton(f"⭐  {tr('favorites_category')}   ·  {len(self.favorites)}")
        favorites_button.setObjectName("CategoryButton")
        favorites_button.setCursor(Qt.CursorShape.PointingHandCursor)
        favorites_button.clicked.connect(lambda: self.set_category(FAVORITES_CATEGORY_ID))
        self.category_buttons.append(favorites_button)
        self.favorites_button = favorites_button
        self.category_ids.append(FAVORITES_CATEGORY_ID)
        sidebar_layout.addWidget(favorites_button)

        sidebar_layout.addStretch(1)
        area_layout.addWidget(sidebar)

        content_body = QWidget()
        content_layout = QVBoxLayout(content_body)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        self.content_title = QLabel()
        self.content_title.setStyleSheet("font-size: 19pt; font-weight: 900; color: #FAFAFF; letter-spacing: -0.4px;")
        content_layout.addWidget(self.content_title)

        cards_scroll = QScrollArea()
        cards_scroll.setObjectName("CardsScroll")
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        cards_container = QWidget()
        cards_container.setObjectName("CardsContainer")
        self.cards_layout = QVBoxLayout(cards_container)
        self.cards_layout.setContentsMargins(0, 0, 16, 0) 
        self.cards_layout.setSpacing(16)
        cards_scroll.setWidget(cards_container)

        content_layout.addWidget(cards_scroll, stretch=1)
        area_layout.addWidget(content_body, stretch=1)

        return area_layout

    def build_status_bar(self) -> QWidget:
        status_widget = QWidget()
        layout = QHBoxLayout(status_widget)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        status_widget.setStyleSheet(
            "background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.06); border-radius: 22px;"
        )

        self.status_text = QLabel()
        self.status_text.setStyleSheet("color: #9CA3AF; font-size: 10pt; font-weight: bold; border: none;")
        layout.addWidget(self.status_text)
        self.status_bar_layout = layout
        return status_widget

    def set_category(self, category_id: str) -> None:
        self.active_category = category_id
        for button, button_id in zip(self.category_buttons, self.category_ids):
            button.setObjectName("CategoryActive" if button_id == category_id else "CategoryButton")
            button.style().unpolish(button)
            button.style().polish(button)
        self.load_cards(animate=True)

    def on_search_text_changed(self, _text: str) -> None:
        # Wait until the user pauses typing before rebuilding the card list —
        # rebuilding on every keystroke was the main source of the stutter.
        self._search_debounce.start(180)

    def _clear_cards(self) -> None:
        # Stop the shared reveal queue and any pending per-card timers/animations
        # BEFORE detaching widgets, so a delayed callback never touches a deleted card.
        self._reveal_timer.stop()
        self._reveal_queue.clear()
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                if isinstance(widget, ProgramCard):
                    widget.cancel_pending()
                widget.setParent(None)
                widget.deleteLater()

    def _reveal_next_card(self) -> None:
        if not self._reveal_queue:
            self._reveal_timer.stop()
            return
        card = self._reveal_queue.pop(0)
        try:
            card.play_entrance_animation()
        except RuntimeError:
            pass

    def load_cards(self, animate: bool = True) -> None:
        self._clear_cards()

        term = self.search_input.text().strip().lower()
        
        # Если в поиске есть лупа (от перевода), очищаем
        if "🔍" in term:
            term = term.replace("🔍", "").strip()

        matches = []
        for program in self.programs:
            if self.active_category == FAVORITES_CATEGORY_ID:
                if program.get("name") not in self.favorites:
                    continue
            elif self.active_category != "all" and program.get("category") != self.active_category:
                continue
            description = localized(program.get("description", ""), tr.lang)
            if term and term not in program.get("name", "").lower() and term not in description.lower():
                continue
            matches.append(program)

        category_name = tr("all_programs")
        if self.active_category != "all":
            category_name = self.category_display_name(self.active_category)
        self.content_title.setText(tr("content_title_found", category=category_name, n=len(matches)))

        if not matches:
            empty_label = QLabel(tr("empty_state"))
            empty_label.setObjectName("EmptyState")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(empty_label)
            self.cards_layout.addStretch(1)
            return

        # Only the first batch gets the staggered fade-in — long lists (or a filtered
        # re-search) show instantly instead of queuing dozens of animations at once.
        max_animated = 24
        for index, program in enumerate(matches):
            category_name_for_card = self.category_display_name(program.get("category", ""))
            card = ProgramCard(
                program,
                category_name_for_card,
                performance_mode=self.performance_mode,
                is_favorite=program.get("name") in self.favorites,
            )
            card.download_button.clicked.connect(lambda checked, p=program: self.start_download(p))
            card.favorite_toggled.connect(self.on_favorite_toggled)
            self.cards_layout.addWidget(card)
            if animate and not self.performance_mode and index < max_animated:
                self._reveal_queue.append(card)

        self.cards_layout.addStretch(1)
        if self._reveal_queue:
            self._reveal_timer.start()

    def on_favorite_toggled(self, program_name: str, is_favorite: bool) -> None:
        if is_favorite:
            self.favorites.add(program_name)
        else:
            self.favorites.discard(program_name)
        self.app_settings["favorites"] = sorted(self.favorites)
        save_app_settings(self.root, self.app_settings)
        if hasattr(self, "favorites_button"):
            self.favorites_button.setText(f"⭐  {tr('favorites_category')}   ·  {len(self.favorites)}")
        if self.active_category == FAVORITES_CATEGORY_ID and not is_favorite:
            self.load_cards(animate=False)

    def start_download(self, program: Dict) -> None:
        if self.download_in_progress:
            QMessageBox.information(self, tr("download_in_progress_title"), tr("download_in_progress_text"))
            return

        url = program.get("url", "")
        if not url or url not in self.whitelist:
            QMessageBox.warning(self, tr("error_title"), tr("whitelist_error"))
            return

        if QtCore.QSysInfo.productType() not in ("windows",) and sys.platform != "win32":
            QMessageBox.warning(self, tr("error_title"), tr("platform_error"))
            return

        file_name_base = sanitize_filename(program["name"].replace(" ", "_"))
        destination_base = self.download_folder / file_name_base

        confirm = QMessageBox.question(
            self,
            tr("confirm_title"),
            tr("confirm_text", name=program["name"], url=url),
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.download_in_progress = True
        self.set_download_status(tr("downloading_status", name=program["name"]))
        self.progress_bar.setValue(0)

        self.download_thread = DownloadWorker(url=url, base_dest=destination_base)
        self.download_thread.progress_changed.connect(self.update_download_progress)
        self.download_thread.finished.connect(self.download_completed)
        self.download_thread.error.connect(self.download_failed)
        self.download_thread.start()

    def update_download_progress(self, percent: int, speed: float) -> None:
        self.progress_bar.setValue(percent)
        speed_text = format_bytes(int(speed)) + "/s"
        self.set_download_status(tr("download_progress_status", percent=percent, speed=speed_text))

    def download_completed(self, path: Path) -> None:
        self.download_in_progress = False
        self.progress_bar.setValue(100)
        self.set_download_status(tr("download_done_status", name=path.name))
        msg = QMessageBox(self)
        msg.setWindowTitle(tr("done_title"))
        msg.setText(tr("done_text", path=path))
        open_folder = msg.addButton(tr("open_folder_btn"), QMessageBox.ButtonRole.AcceptRole)
        run_file = msg.addButton(tr("run_file_btn"), QMessageBox.ButtonRole.AcceptRole)
        msg.addButton(tr("close_btn"), QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        if msg.clickedButton() == open_folder:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path.parent)))
        elif msg.clickedButton() == run_file:
            if path.exists():
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))

    def download_failed(self, message: str) -> None:
        self.download_in_progress = False
        self.set_download_status(tr("download_error_status"))
        QMessageBox.critical(self, tr("error_title"), tr("download_error_text", error=message))

    def set_download_status(self, message: str) -> None:
        self.status_text.setText(message)

    def show_about_dialog(self) -> None:
        about = QMessageBox(self)
        about.setWindowTitle(tr("about_title"))
        about.setIconPixmap(get_brand_pixmap(84))
        about.setText(tr("about_html", brand=BRANDING, app=APP_NAME, version=VERSION, contact=CONTACT_EMAIL))
        about.setStandardButtons(QMessageBox.StandardButton.Ok)
        about.exec()

    def closeEvent(self, event) -> None:
        # A download running in the background can otherwise emit a signal after
        # the window (and its slots) are gone — that's one of the occasional crashes.
        self._reveal_timer.stop()
        self._search_debounce.stop()
        if self.download_thread is not None:
            try:
                self.download_thread.progress_changed.disconnect()
                self.download_thread.finished.disconnect()
                self.download_thread.error.disconnect()
            except TypeError:
                pass
        super().closeEvent(event)

def install_crash_logger(app_root: Path) -> None:
    import traceback

    log_path = app_root / "error_log.txt"

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n--- {time.ctime()} ---\n{text}")
        except OSError:
            pass
        try:
            QMessageBox.critical(
                None,
                tr("crash_title"),
                tr("crash_text", error=exc_value, logname=log_path.name),
            )
        except Exception:
            pass

    sys.excepthook = handle_exception

def main() -> None:
    global APP_ICON_PATH

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    app_root = app_root_path()
    install_crash_logger(app_root)

    resource_root = resource_path()

    APP_ICON_PATH = resolve_app_icon_path(resource_root, app_root)
    app_icon = QIcon(str(APP_ICON_PATH)) if APP_ICON_PATH is not None else None
    if app_icon is not None:
        app.setWindowIcon(app_icon)

    tr.set_language(load_language_preference(app_root))

    if not validate_launch(app_root):
        sys.exit(1)

    ensure_portable_cache(app_root)
    data = load_program_data(resource_root)

    window = MainWindow(app_root, data)
    if app_icon is not None:
        window.setWindowIcon(app_icon)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()