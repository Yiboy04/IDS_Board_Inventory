# LED Board Manager Bootstrap Installer
# Prompts for install folder and data storage location, downloads project from GitHub, sets config, creates shortcut.

param(
    [string]$RepoZipUrl = "https://github.com/<owner>/<repo>/archive/refs/heads/main.zip",
    [string]$AppName = "LED Board Manager"
)

$ErrorActionPreference = 'Stop'

function Choose-Folder([string]$title, [string]$defaultPath) {
    Add-Type -AssemblyName System.Windows.Forms
    $f = New-Object System.Windows.Forms.FolderBrowserDialog
    $f.Description = $title
    $f.SelectedPath = $defaultPath
    if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $f.SelectedPath
    }
    throw "Folder selection cancelled"
}

# 1) Prompt install folder (no admin required)
$defaultInstall = Join-Path $env:LOCALAPPDATA $AppName
$installDir = Choose-Folder "Choose installation folder" $defaultInstall
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

# 2) Prompt data storage folder
$defaultData = Join-Path $env:LOCALAPPDATA "$AppName-data"
$dataDir = Choose-Folder "Choose where to store app data" $defaultData
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

# 3) Download latest project ZIP from GitHub
$zipPath = Join-Path $env:TEMP "$AppName.zip"
Write-Host "Downloading from: $RepoZipUrl"
Invoke-WebRequest -Uri $RepoZipUrl -OutFile $zipPath

# 4) Extract into install folder
Write-Host "Extracting to: $installDir"
Expand-Archive -Path $zipPath -DestinationPath $installDir -Force
Remove-Item $zipPath -Force

# 5) Find project root (first folder in extracted archive)
$extractedRoot = Get-ChildItem -Path $installDir -Directory | Select-Object -First 1
if (-not $extractedRoot) { throw "Extraction failed: no folder found" }
$projDir = $extractedRoot.FullName

# 6) Write config.json with data_dir
$configPath = Join-Path $projDir 'config.json'
@{ data_dir = $dataDir } | ConvertTo-Json | Set-Content -Encoding UTF8 $configPath

# 7) Create venv and install optional packages
$py = 'python'
try { $py = (Get-Command python).Source } catch {}
Push-Location $projDir
& $py -m venv .venv
$venvPy = Join-Path $projDir '.venv\Scripts\python.exe'
& $venvPy -m pip install --upgrade pip
# Optional packages for icon/packaging
try { & $venvPy -m pip install pillow } catch {}
Pop-Location

# 8) Create Desktop shortcut to launch GUI
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = Join-Path $desktop "$AppName.lnk"
$shortcut = $shell.CreateShortcut($lnk)
$shortcut.TargetPath = (Join-Path $projDir '.venv\Scripts\pythonw.exe')
$shortcut.Arguments = 'Main.py gui'
$shortcut.WorkingDirectory = $projDir
$shortcut.Description = $AppName
$iconCandidate = Join-Path $projDir 'assets\app.ico'
if (Test-Path $iconCandidate) { $shortcut.IconLocation = "$iconCandidate,0" }
$shortcut.Save()

Write-Host "Installed to: $projDir"
Write-Host "Data stored at: $dataDir"
Write-Host "Shortcut created: $lnk"
