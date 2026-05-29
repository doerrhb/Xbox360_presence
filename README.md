# RGH Xbox 360 Discord Rich Presence (Windows Tray Edition)

![example](media/example.png)

### 📢 Attribution & Enhancement Note
This repository is an **enhanced fork and extension** of the original CLI script by [zanesix/Xbox360_presence](https://github.com/zanesix/Xbox360_presence). 

The original command-line Python script has been restructured and packaged into a full-featured, background Windows application that runs in the system tray, installs to `Program Files`, and can run automatically at startup.

---

This application updates your Discord Rich Presence with the game currently being played on your modded Xbox 360 running the Aurora dashboard with the Nova plugin active.

## 🚀 Key Improvements & Features

*   **Sleek System Tray Application**: Runs completely in the background within the Windows system tray (`avatar.ico`).
*   **Complete Windows Installer**: Built-in script using Inno Setup compiles the app to `Program Files` and adds it to the Start Menu.
*   **Automatic Windows Startup**: Toggle running at Windows sign-in with a single click (handled safely via registry keys).
*   **Graphical Configuration**: Easy configuration dialog launched from the tray menu (no need to open text files manually).
*   **User Config Isolation**: Saves settings to `%APPDATA%\Xbox360 Presence\config.ini` so local credentials and settings are kept separate from the code repository.
*   **Original CLI Preserved**: The foreground CLI behavior remains fully operational for direct script runners in `rich_presence.py`.
*   **Playtime tracking**: Shows elapsed playtime in a human-readable format, updating every 15 seconds.
*   **Custom Images**: Automatically displays matching game icons using Title IDs from the Xbox Unity database, falling back gracefully to default images.

---

## 🛠️ Requirements

*   A modded Xbox 360 running the Aurora dashboard with the **Nova plugin** active.
*   Your own [Discord Application Client ID](https://discord.com/developers/applications).
*   Python 3.x installed (if running from source).
*   Dependencies listed in `requirements.txt` (installed automatically in the EXE release).

---

## 💻 Installation & Setup

### Option 1: Install the Windows App (Recommended)
1. Build or download the setup executable `Xbox360PresenceSetup.exe` (see [Building the Installer](#building-the-exe-and-installer)).
2. Run the installer. It will:
    *   Install the application to `C:\Program Files\Xbox360 Presence` (or your user's equivalent directory).
    *   Create a Start Menu shortcut named **Xbox360 Presence**.
    *   Optionally register the app to run automatically when your Windows user signs in.
3. Start the application from the Start Menu. Right-click the green Xbox tray icon, select **Configure...**, and enter your details.

### Option 2: Running from Source
1. **Clone this repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/Xbox360_presence.git
    cd Xbox360_presence
    ```
2. **Install the required Python libraries:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Run the Tray App:**
    ```bash
    python xbox360_presence_tray.py
    ```

---

## ⚙️ Configuration

The application requires your Discord Application Client ID and your Xbox 360's IP address.

### Discord Application Client ID Setup
1. Sign into the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a **New Application** and name it (e.g., `Xbox 360 Hardware`). The name of the application will show up as your active "game" status in Discord.
3. Copy your application **Client ID** from the application's General Information tab.

### Configuring the App
*   **Using the Tray App**: Right-click the tray icon and choose **Configure...** to input your Client ID and Xbox IP address. This saves to `%APPDATA%\Xbox360 Presence\config.ini`.
*   **Using Command Line**: If running `rich_presence.py` directly, you can create a local `config.ini` file in the project folder with this content:
    ```ini
    [discord]
    client_id = YOUR_CLIENT_ID_HERE

    [xbox]
    ip_address = YOUR_XBOX_IP_HERE
    ```

---

## 🎯 Usage

### System Tray Controls
Right-click the Xbox logo icon in the system tray to access controls:
*   **Status display**: Shows connection and activity status (e.g., "Status: Playing Aurora", "Status: Stopped").
*   **Start / Stop / Restart Rich Presence**: Manually control the RPC background worker.
*   **Configure...**: Open the graphical configuration dialog.
*   **Open Config Folder**: Opens `%APPDATA%\Xbox360 Presence\` in Windows Explorer to inspect log/config files.
*   **Run at Windows startup**: Toggles whether the app starts automatically upon signing into Windows.
*   **Exit**: Disconnects from Discord and terminates the background process cleanly.

### Command Line Mode
You can still run the foreground CLI script directly:
```bash
# Uses the IP address defined in config.ini
python rich_presence.py

# Overrides the config.ini IP address with a command-line argument
python rich_presence.py 192.168.0.69
```

---

## 🔨 Building the EXE and Installer

To bundle the application yourself, you need to install the development dependencies (`pip install pyinstaller pystray pillow requests pypresence`).

### 1. Build the Tray EXE
Run the PowerShell script:
```powershell
.\build_exe.ps1
```
This uses PyInstaller to compile the python files and assets into a single standalone executable located at:
```text
dist\Xbox360Presence.exe
```

### 2. Compile the Installer
Ensure you have [Inno Setup 6](https://jrsoftware.org/isinfo.php) installed on your system. Run:
```powershell
.\build_installer.ps1
```
This compiles the executable and assets into a professional setup wizard at:
```text
dist\installer\Xbox360PresenceSetup.exe
```

---

## 📝 License & Acknowledgments

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

### Acknowledgments & Credits
*   **Original CLI Tool**: Developed by [zanesix](https://github.com/zanesix/Xbox360_presence).
*   [Aurora Dashboard](http://phoenix.xboxunity.net/): A custom dashboard replacement for Xbox 360.
*   [Xbox Unity](http://www.xboxunity.net/): Database and host for Xbox game images and metadata.
*   [Nova Plugin](http://phoenix.xboxunity.net/): Enables the Xbox 360 Web UI and HTTP endpoints.
*   [albertofustinoni](https://gist.githubusercontent.com/albertofustinoni/51f2ea0537130f4820a3f5ed49d69042/raw/9ffead88e369a40e120082ef385efea6fc1cbb81/Xbox360TitleIDs.json): Curated source mapping Xbox Title IDs to Game Titles.
