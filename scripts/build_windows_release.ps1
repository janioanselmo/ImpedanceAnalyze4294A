param(
    [string]$AppName = "ImpedanceAnalyzer4294A-IEB-UFSC"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$PyInstaller = Join-Path $Root ".venv\Scripts\pyinstaller.exe"
$Dist = Join-Path $Root "dist"
$Build = Join-Path $Root "build"
$InstallerBuild = Join-Path $Build "installer"
$PortableDir = Join-Path $Dist $AppName
$PortableZip = Join-Path $Dist "$AppName-portable.zip"
$SetupExe = Join-Path $Dist "$AppName-Setup.exe"
$SetupBat = Join-Path $Dist "$AppName-Setup.bat"
$PayloadZip = Join-Path $InstallerBuild "$AppName.zip"

if (!(Test-Path -LiteralPath $Python)) {
    throw "Virtual environment not found. Run run_windows.bat once before building."
}

& $Python -m PyInstaller --version | Out-Null

New-Item -ItemType Directory -Force -Path $Dist, $Build, $InstallerBuild | Out-Null

if (Test-Path -LiteralPath $PortableDir) {
    Remove-Item -LiteralPath $PortableDir -Recurse -Force
}
if (Test-Path -LiteralPath (Join-Path $Build $AppName)) {
    Remove-Item -LiteralPath (Join-Path $Build $AppName) -Recurse -Force
}

& $PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name $AppName `
    --distpath $Dist `
    --workpath $Build `
    --collect-all matplotlib `
    --collect-all PyQt5 `
    --collect-all pyvisa `
    --collect-all pyvisa_py `
    --collect-all pyvisa_sim `
    --add-data "samples;samples" `
    (Join-Path $Root "script.py")

if (!(Test-Path -LiteralPath (Join-Path $PortableDir "$AppName.exe"))) {
    throw "PyInstaller did not create $AppName.exe."
}

if (Test-Path -LiteralPath $PortableZip) {
    Remove-Item -LiteralPath $PortableZip -Force
}
Compress-Archive -Path $PortableDir -DestinationPath $PortableZip -Force

Remove-Item -LiteralPath $InstallerBuild -Recurse -Force
New-Item -ItemType Directory -Force -Path $InstallerBuild | Out-Null
Copy-Item -LiteralPath $PortableZip -Destination $PayloadZip -Force

$InstallCmd = Join-Path $InstallerBuild "setup.cmd"
@"
@echo off
set APP_NAME=$AppName
set TARGET_ROOT=%LOCALAPPDATA%\Programs
set TARGET=%TARGET_ROOT%\%APP_NAME%

if exist "%TARGET%" rmdir /s /q "%TARGET%"
mkdir "%TARGET_ROOT%" >nul 2>nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%~dp0$AppName.zip' -DestinationPath '%TARGET_ROOT%' -Force"
powershell -NoProfile -ExecutionPolicy Bypass -Command "`$desktop=[Environment]::GetFolderPath('Desktop'); `$shell=New-Object -ComObject WScript.Shell; `$shortcut=`$shell.CreateShortcut((Join-Path `$desktop '$AppName.lnk')); `$shortcut.TargetPath=(Join-Path `$env:LOCALAPPDATA 'Programs\$AppName\$AppName.exe'); `$shortcut.WorkingDirectory=(Join-Path `$env:LOCALAPPDATA 'Programs\$AppName'); `$shortcut.Save()"

start "" "%TARGET%\%APP_NAME%.exe"
"@ | Set-Content -LiteralPath $InstallCmd -Encoding ASCII

@"
@echo off
setlocal
set APP_NAME=$AppName
set SOURCE_ZIP=%~dp0$AppName-portable.zip
set TARGET_ROOT=%LOCALAPPDATA%\Programs
set TARGET=%TARGET_ROOT%\%APP_NAME%

if not exist "%SOURCE_ZIP%" (
  echo Could not find "%SOURCE_ZIP%".
  pause
  exit /b 1
)

if exist "%TARGET%" rmdir /s /q "%TARGET%"
mkdir "%TARGET_ROOT%" >nul 2>nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%SOURCE_ZIP%' -DestinationPath '%TARGET_ROOT%' -Force"
powershell -NoProfile -ExecutionPolicy Bypass -Command "`$desktop=[Environment]::GetFolderPath('Desktop'); `$shell=New-Object -ComObject WScript.Shell; `$shortcut=`$shell.CreateShortcut((Join-Path `$desktop '$AppName.lnk')); `$shortcut.TargetPath=(Join-Path `$env:LOCALAPPDATA 'Programs\$AppName\$AppName.exe'); `$shortcut.WorkingDirectory=(Join-Path `$env:LOCALAPPDATA 'Programs\$AppName'); `$shortcut.Save()"

echo Installed %APP_NAME% to "%TARGET%".
start "" "%TARGET%\%APP_NAME%.exe"
endlocal
"@ | Set-Content -LiteralPath $SetupBat -Encoding ASCII

$SedPath = Join-Path $InstallerBuild "$AppName.sed"
$EscapedSetup = $SetupExe.Replace("\", "\\")
$EscapedInstallerBuild = ($InstallerBuild + "\").Replace("\", "\\")
@"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=0
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=
DisplayLicense=
FinishMessage=Installation complete.
TargetName=$EscapedSetup
FriendlyName=$AppName
AppLaunched=setup.cmd
PostInstallCmd=<None>
AdminQuietInstCmd=setup.cmd
UserQuietInstCmd=setup.cmd
SourceFiles=SourceFiles
[SourceFiles]
SourceFiles0=$EscapedInstallerBuild
[SourceFiles0]
setup.cmd=
$AppName.zip=
"@ | Set-Content -LiteralPath $SedPath -Encoding ASCII

if (Test-Path -LiteralPath $SetupExe) {
    Remove-Item -LiteralPath $SetupExe -Force
}

& iexpress.exe /N $SedPath

if (!(Test-Path -LiteralPath $SetupExe)) {
    Write-Warning "IExpress did not create the setup executable. Use $SetupBat with $PortableZip."
} else {
    Get-Item -LiteralPath $SetupExe
}

Get-Item -LiteralPath (Join-Path $PortableDir "$AppName.exe")
Get-Item -LiteralPath $PortableZip
Get-Item -LiteralPath $SetupBat
