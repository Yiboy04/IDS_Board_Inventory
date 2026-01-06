; Inno Setup Script for LED Board Manager Bootstrap Installer
; Requires Inno Setup (https://jrsoftware.org/isinfo.php)

#define AppName "LED Board Manager"
#define AppVersion "1.0.0"
#define Publisher "Your Name"
#define InstallExeName "setup.exe"
#define DefaultDirName "{localappdata}\\LED Board Manager"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={#DefaultDirName}
DisableDirPage=no
OutputDir=dist-installer
OutputBaseFilename={#InstallExeName}
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "installer\\setup_bootstrap.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File \"{app}\\setup_bootstrap.ps1\" -RepoZipUrl \"https://github.com/<owner>/<repo>/archive/refs/heads/main.zip\" -AppName \"LED Board Manager\""; StatusMsg: "Running bootstrap..."; Flags: runhidden

[Icons]
Name: "{group}\LED Board Manager"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File \"{app}\\setup_bootstrap.ps1\" -RepoZipUrl \"https://github.com/<owner>/<repo>/archive/refs/heads/main.zip\" -AppName \"LED Board Manager\""; WorkingDir: "{app}"; IconFilename: "{app}\\..\\assets\\app.ico"
Name: "{commondesktop}\LED Board Manager"; Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File \"{app}\\setup_bootstrap.ps1\" -RepoZipUrl \"https://github.com/<owner>/<repo>/archive/refs/heads/main.zip\" -AppName \"LED Board Manager\""; WorkingDir: "{app}"; IconFilename: "{app}\\..\\assets\\app.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
