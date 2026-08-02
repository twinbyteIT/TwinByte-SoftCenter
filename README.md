# TwinByte SoftCenter

TwinByte SoftCenter is a modern, portable, and efficient software download hub designed for quick and secure access to essential utilities.

##   📺 Demo Video
[![Watch the video](https://img.youtube.com/vi/o8yiGGLeZ7U/0.jpg)](https://www.youtube.com/watch?v=o8yiGGLeZ7U)

*Click the image above to watch the TwinByte SoftCenter presentation on YouTube.*

## 🚀 Key Features

*   **Ultra Portable**: Runs without installation.
*   **Modern UI**: Sleek Glassmorphism design with hardware-accelerated animations (shadows, transitions) and a performance mode for low-end hardware.
*   **Multilingual**: Native support for Russian, English, Polish, and Ukrainian with automatic system language detection.
*   **Security Focused**: Strictly loads software from a pre-verified Whitelist.
*   **Rich Functionality**:
    *   Intuitive category-based navigation.
    *   Favorites system to save preferred tools.
    *   Real-time search capabilities.
    *   Live download progress and speed monitoring.
    *   Customizable download directory settings.

## 🛠 Tech Stack

*   **Language**: Python 3
*   **GUI**: PyQt6
*   **Networking**: Requests
*   **Build**: Optimized for PyInstaller packaging

## 📋 Requirements

*   **OS**: Windows 10/11
*   **Dependencies**:
    *   `PyQt6`
    *   `requests`

## ⚙️ Setup & Usage

1. **Launch**: Ensure the application is executed from a folder that adheres to the naming conventions (must contain "twinbyte" or "softcenter" in the path).
2. **Database**: Applications are managed via the `programs.json` file in the root directory.
3. **Settings**: User preferences (language, favorites, display mode) are automatically stored in `TwinByteSoftCenter/settings.json`.

## 🛡 Security & Safety

The application includes built-in protection layers:
*   Blocks execution from temporary directories (Temp folders).
*   Validates all file names and paths.
*   Whitelisting mechanism to prevent unauthorized URL access.
  
## 🛡 Security Status
![VirusTotal Scan](https://img.shields.io/badge/VirusTotal-Clean-green?logo=virustotal)
*All releases are scanned with VirusTotal to ensure 100% security for the end user.*

## 🏗 Building from Source

If you prefer to compile the application yourself to ensure complete security, follow these steps:

### Prerequisites
*   Python 3.x installed on your system.
*   `PyInstaller` installed (`pip install pyinstaller`).

### Build Command
Run the following command in the project root directory:

```bash
pyinstaller --noconfirm --onefile --windowed --icon=TwinByte_SoftCenter.ico --add-data "programs.json;." --add-data "TwinByte_SoftCenter.ico;." --version-file=version_info.txt --name "TwinByte SoftCenter" TwinByteSoftCenter.py
```

## 📩 Contact

For inquiries, reach out to: [twinbytecontact@gmail.com](mailto:twinbytecontact@gmail.com)

---
© 2026 TwinByte IT. All rights reserved.
