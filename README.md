# LED Board Note Storage (Python CLI)

A simple Python CLI to store LED board info in a local "note" file using JSON Lines (one JSON object per line).

## Fields
- Board ID (string)
- Board name (string)
- Board IC (example: SM1627P)
- Board DC (example: 74HC 368)
- Board size (string, free-form)

## Data Storage
Data is saved in `data/boards_note.jsonl` relative to this project folder. If the file or folder doesn't exist, it's created automatically.

## Usage
From the project folder, run:

```powershell
# Add a board
python Main.py add --id B001 --name "Main Display" --ic SM1627P --dc "74HC 368" --size "320x160"

# List all boards
python Main.py list

# Show one board by ID
python Main.py show --id B001

# Delete a board by ID
python Main.py delete --id B001
```

### Interactive mode (Run button / no args)
If you press "Run Python File" in VS Code or run without arguments, an interactive menu appears where you can list, add, show, or delete boards.

## GUI Application
- Launch GUI by pressing "Run Python File" (no arguments) or:
```powershell
python Main.py gui
```
- Features:
	- Add/Update via form fields (ID, Name, IC, DC, Size)
	- View button to show full board details in a popup
	- Delete selected board
	- Table view of all boards
	- Auto-refresh and select-to-fill form
	- Login screen deciding role (admin or employee)
	- Admin-only Employees tab to add/update/delete employee accounts
	- Board Issues dialog to record quantities for common issues (caterpillar, lamp pixel drop/problem, kaki patah, RGB line, box problem, module blackout, broken module/connector/power socket, wiring, broken frame)
	- Two checkboxes in Issues: "No issue" (zeros all quantities) and "Total loss" (marks the board as fully failed)
	- "Added by" is recorded for each board (who saved it)
	- Quotations page: build a quotation list and export to Excel (.xlsx) or CSV. For Excel export, install `openpyxl`.

Notes:
- The GUI uses Tkinter (included with standard Python on Windows).
- Data is the same `data/boards_note.jsonl` used by the CLI.

## Login and Roles
- Admin credentials:
	- Username: `admin`
	- Password: `Too@686868`
- Employees:
	- Stored in `data/employees_note.jsonl` (created automatically)
	- Admin can add/update/delete employees in the Employees tab
	- Employees can log in and use the Boards tab but cannot manage employees

## Notes
- The tool prevents duplicate IDs on add.
- The note file uses JSONL to keep things simple and human-editable.
- No external dependencies required (Python 3.8+).

## Desktop Shortcut
- A Windows desktop shortcut named "LED Board Manager" has been created to launch the GUI directly.
- If you need to recreate it manually, run in PowerShell:
```powershell
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = Join-Path $desktop 'LED Board Manager.lnk'
$shortcut = $shell.CreateShortcut($lnk)
$shortcut.TargetPath = 'C:\\Users\\tehzh\\OneDrive\\Desktop\\Intern\\Project\\.venv\\Scripts\\pythonw.exe'
$shortcut.Arguments = 'Main.py gui'
$shortcut.WorkingDirectory = 'C:\\Users\\tehzh\\OneDrive\\Desktop\\Intern\\Project'
$shortcut.Description = 'LED Board Manager'
$shortcut.IconLocation = 'C:\\Users\\tehzh\\OneDrive\\Desktop\\Intern\\Project\\assets\\app.ico,0'
$shortcut.Save()
```

## Packaging for Other Devices
- Option 1 (Python installed): Copy the project folder and run with that device's Python.
	- Ensure Python 3.8+ installed, then:
```powershell
python Main.py gui
```
- Install dependencies (needed for Excel export and logos):
```powershell
python -m pip install -r requirements.txt
```
- Option 2 (standalone EXE with PyInstaller):
	1) Install PyInstaller in your venv:
```powershell
C:\\Users\\tehzh\\OneDrive\\Desktop\\Intern\\Project\\.venv\\Scripts\\python.exe -m pip install pyinstaller
```
	2) Build the executable (uses the icon if present):
```powershell
C:\\Users\\tehzh\\OneDrive\\Desktop\\Intern\\Project\\.venv\\Scripts\\python.exe -m PyInstaller --onefile --noconsole --name LEDBoardManager --hidden-import login_gui --icon assets\\app.ico Main.py
```
	- If you don't have `assets/app.ico` yet, see "Icon Setup" below.

	## Icon Setup
	- Save your source image (e.g., the fox logo) as `assets/logo_source.png`.
	- Install Pillow and build the `.ico` with background removal:
	```powershell
	C:\\Users\\tehzh\\OneDrive\\Desktop\\Intern\\Project\\.venv\\Scripts\\python.exe -m pip install pillow
	C:\\Users\\tehzh\\OneDrive\\Desktop\\Intern\\Project\\.venv\\Scripts\\python.exe icon_tools.py --source assets\\logo_source.png --out assets\\app.ico
	```
	- After creating `assets/app.ico`, re-run the shortcut creation or include the icon in PyInstaller using `--icon assets\\app.ico`.
	3) Distribute `dist/LEDBoardManager.exe` and the `data` folder together.
	4) Create a desktop shortcut pointing to `LEDBoardManager.exe`.

Notes:
- `--noconsole` hides the terminal window when launching the GUI.
- The app stores data next to the executable in the `data` folder.
 - Excel export uses openpyxl; if missing, the app falls back to CSV.
