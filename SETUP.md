# LED Board Manager – Setup Guide (Windows)

This guide helps anyone download, set up, and run the LED Board Manager app on Windows.

## Prerequisites
- Windows 10/11
- Python 3.8+ (recommend 3.10/3.11)
- Git (optional, for cloning)

## 1) Get the project
- Option A: Clone via Git
```powershell
git clone <your_repo_url>
cd Project
```
- Option B: Download ZIP from GitHub and extract the folder.

## 2) Create a virtual environment
From the project folder:
```powershell
python -m venv .venv
```
Activate it (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```
If activation is blocked, either run without activation or temporarily bypass policy:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
```

## 3) Run the application (GUI)
You can run the GUI directly with the venv Python:
```powershell
.\.venv\Scripts\python.exe Main.py gui
```
Or, after activation:
```powershell
python Main.py gui
```
- Admin login: username `admin`, password `Too@686868`
- Employees are managed by admin in the Employees tab.

## 4) Optional: App icon setup
If you have a source image (e.g., a PNG logo), place it at `assets/logo.png`.
Install Pillow (only needed for icon building):
```powershell
.\.venv\Scripts\python.exe -m pip install pillow
```
Build an `.ico` with white-background removal:
```powershell
.\.venv\Scripts\python.exe icon_tools.py --source assets\logo.png --out assets\app.ico
```
The GUI will use `assets/app.ico` automatically. Packaging steps below can also embed this icon.

## 5) Optional: Desktop shortcut
Create a Desktop shortcut that launches the GUI with the icon:
```powershell
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = Join-Path $desktop 'LED Board Manager.lnk'
$shortcut = $shell.CreateShortcut($lnk)
$shortcut.TargetPath = "$PWD\\.venv\\Scripts\\pythonw.exe"
$shortcut.Arguments = 'Main.py gui'
$shortcut.WorkingDirectory = "$PWD"
$shortcut.Description = 'LED Board Manager'
$shortcut.IconLocation = "$PWD\\assets\\app.ico,0"
$shortcut.Save()
```
If the icon looks blank, restart Explorer to refresh icon cache:
```powershell
Stop-Process -Name explorer -Force
Start-Process explorer.exe
```

## 6) Optional: Build a standalone EXE (distribution)
Install PyInstaller:
```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
```
Build with embedded icon and hidden console:
```powershell
.\.venv\Scripts\python.exe -m PyInstaller --onefile --noconsole --name LEDBoardManager --hidden-import login_gui --icon assets\app.ico Main.py
```
- The executable will be at `dist/LEDBoardManager.exe`.
- Copy the `data` folder alongside the EXE for persisted notes.
- Create a desktop shortcut pointing to `dist/LEDBoardManager.exe` (same script as above, set `TargetPath` to the EXE).

## Data storage
- Boards are stored in `data/boards_note.jsonl`.
- Employees are stored in `data/employees_note.jsonl`.
- Files are created automatically on first run.

## Troubleshooting
- Execution policy blocks activation:
  - Use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force` or run with `.venv\Scripts\python.exe` directly.
- Missing `tkinter`:
  - Ensure you installed the standard Python from python.org; it includes Tk on Windows.
- Icon not applied:
  - Verify `assets/app.ico` exists and re-create the shortcut.
- VS Code run button:
  - Script launches the GUI by default with no arguments.

## Project files
- [Main.py](Main.py): CLI + app entry point.
- [login_gui.py](login_gui.py): Tkinter GUI with login and role-based tabs.
- [icon_tools.py](icon_tools.py): converts PNG to `.ico` and removes white background.
- [README.md](README.md): quick usage overview.
- `assets/`: icons and images.
- `data/`: note files (JSON Lines).

## Setup.exe (Bootstrap Installer)
If you want a single setup.exe that installs from GitHub and asks where to store data:

1) Update the repo URL in [installer/installer.iss](installer/installer.iss) (replace `<owner>/<repo>`):
   - `https://github.com/<owner>/<repo>/archive/refs/heads/main.zip`

2) Install Inno Setup (https://jrsoftware.org/isinfo.php).

3) Build the installer:
```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\installer.iss
```
- The output setup.exe will be in `dist-installer/`.
- When run, it:
  - Prompts for install folder and data folder
  - Downloads the project ZIP from GitHub
  - Writes `config.json` with `data_dir`
  - Creates a venv and installs Pillow (optional)
  - Creates a Desktop shortcut to `pythonw.exe Main.py gui`

Note: The app reads `config.json` to find the `data_dir`. You can relocate data later by editing `config.json`.
