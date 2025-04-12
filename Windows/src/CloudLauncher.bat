@echo off

:: Enable ANSI escape sequences for color (Windows 10+)
for /F "delims=" %%A in ('echo prompt $E^|cmd') do set "ESC=%%A"
set "BOLD=%ESC%[1m"
set "BLUE=%ESC%[1;34m"
set "CYAN=%ESC%[1;36m"
set "MAGENTA=%ESC%[1;35m"
set "RESET=%ESC%[0m"
set "GREEN=%ESC%[1;32m"
set "YELLOW=%ESC%[1;33m"
set "RED=%ESC%[1;31m"

:: Set script directory and log file
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "LOGFILE=%SCRIPT_DIR%CloudLauncher.log"
if exist "%LOGFILE%" del "%LOGFILE%"

call :logOnly "Log file location: %LOGFILE%"
call :logOnly "Starting Unified Cloud Launcher..."

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
setlocal enabledelayedexpansion

set "LOCAL_ENV=%SCRIPT_DIR%local_env"

if exist "%LOCAL_ENV%" (
    call :logOnly "Portable Python Environment detected. Skipping installation steps."
    goto provider_selection
)

echo.
echo %BOLD%%YELLOW%-----===[ Cloud GUI Launcher Setup ]===-----%RESET%
echo %GREEN%Brought to you by Techware - Developed by @Proph151Music%RESET%
echo.
echo This will install a local Python environment, dependencies, and Tcl/Tk.
echo.
set /p setupChoice="Do you want to continue setup? (Y/N): "
if /I "!setupChoice!" NEQ "Y" (
    echo.
    echo %RED%Setup canceled by user. Exiting.%RESET%
    pause
    exit /b
)

:: Download Python
call :log Downloading Python embeddable...
set "ZIP_PATH=%TEMP%\\python-embed.zip"
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.3/python-3.13.3-embed-amd64.zip' -OutFile '!ZIP_PATH!'" >> "%LOGFILE%" 2>&1
if not exist "!ZIP_PATH!" (
    call :log ERROR: Failed to download Python embeddable!
    exit /b 1
)
call :log Extracting Python...
powershell -NoProfile -Command "Expand-Archive -Path '!ZIP_PATH!' -DestinationPath '!LOCAL_ENV!' -Force" >> "%LOGFILE%" 2>&1
del "!ZIP_PATH!"

:: Configure _pth
if exist "%LOCAL_ENV%\\python313._pth" (
    powershell -NoProfile -Command "(Get-Content '%LOCAL_ENV%\\python313._pth') -replace '^#\s*import site', 'import site' | Set-Content '%LOCAL_ENV%\\python313._pth'" >> "%LOGFILE%" 2>&1
    powershell -NoProfile -Command "Add-Content -Path '%LOCAL_ENV%\\python313._pth' -Value 'Scripts'" >> "%LOGFILE%" 2>&1
    powershell -NoProfile -Command "Add-Content -Path '%LOCAL_ENV%\\python313._pth' -Value 'Lib'" >> "%LOGFILE%" 2>&1
    powershell -NoProfile -Command "Add-Content -Path '%LOCAL_ENV%\\python313._pth' -Value 'DLLs'" >> "%LOGFILE%" 2>&1
)

:: Download Tcl
set "TCL_ZIP_PATH=%SCRIPT_DIR%tcl.zip"
set "TCL_GITHUB_URL=https://github.com/StardustCollective/HCloud/raw/main/Windows/tcl.zip"
if not exist "%TCL_ZIP_PATH%" (
    powershell -NoProfile -Command "Invoke-WebRequest -Uri '!TCL_GITHUB_URL!' -OutFile '!TCL_ZIP_PATH!'" >> "%LOGFILE%" 2>&1
)
call :log Extracting Tcl/Tk...
powershell -NoProfile -Command "Expand-Archive -Path '%TCL_ZIP_PATH%' -DestinationPath '%LOCAL_ENV%' -Force" >> "%LOGFILE%" 2>&1
del "%TCL_ZIP_PATH%"

:: Install pip
"%LOCAL_ENV%\\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 (
    set "GET_PIP_PATH=%TEMP%\\get-pip.py"
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '!GET_PIP_PATH!'" >> "%LOGFILE%" 2>&1
    "%LOCAL_ENV%\\python.exe" "!GET_PIP_PATH!" >> "%LOGFILE%" 2>&1
    del "!GET_PIP_PATH!"
)

:: Upgrade pip and install all dependencies
"%LOCAL_ENV%\\python.exe" -m pip install --upgrade pip >> "%LOGFILE%" 2>&1
"%LOCAL_ENV%\\python.exe" -m pip install requests paramiko cryptography packaging pywin32 >> "%LOGFILE%" 2>&1

:provider_selection
echo.
echo %BOLD%%GREEN%======================%RESET%
echo %BOLD%%CYAN% Select Cloud Provider %RESET%
echo %BOLD%%GREEN%======================%RESET%
echo.
echo   [1] Hetzner (HCloud)
echo   [2] DigitalOcean (DOCloud)
echo.

set /p choice=Enter your choice [1-2]: 
if "%choice%"=="1" (
    set "TARGET_SCRIPT=HCloud.py"
    set "DOWNLOAD_URL=https://raw.githubusercontent.com/StardustCollective/HCloud/main/HCloud.py"
) else if "%choice%"=="2" (
    set "TARGET_SCRIPT=DOCloud.py"
    set "DOWNLOAD_URL=https://raw.githubusercontent.com/StardustCollective/HCloud/main/DOCloud.py"
) else (
    echo Invalid choice. Exiting...
    goto end
)

IF EXIST "%TARGET_SCRIPT%" (
    echo [D] - Download and Launch %TARGET_SCRIPT%
    echo [L] - Launch local %TARGET_SCRIPT%
    echo [C] - Cancel
    CHOICE /C DLC /N /M "Enter your choice (D, L, or C): "
    IF ERRORLEVEL 3 GOTO :end
    IF ERRORLEVEL 2 GOTO :LAUNCH
    IF ERRORLEVEL 1 GOTO :DOWNLOAD
) ELSE (
    echo.
    echo [D] Download and Launch %TARGET_SCRIPT%
    echo [C] Cancel
    CHOICE /C DC /N /M "Enter your choice (D or C): "
    IF ERRORLEVEL 2 GOTO :end
    IF ERRORLEVEL 1 GOTO :DOWNLOAD
)

:DOWNLOAD
PowerShell -Command "Try {Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%TARGET_SCRIPT%.tmp'; Exit 0} Catch {Exit 1}"
IF EXIST "%TARGET_SCRIPT%.tmp" (
    MOVE /Y "%TARGET_SCRIPT%.tmp" "%TARGET_SCRIPT%" >NUL
)
GOTO :LAUNCH

:LAUNCH
set "PYTHON_EXEC=%LOCAL_ENV%\\pythonw.exe"
if not exist "!PYTHON_EXEC!" set "PYTHON_EXEC=%LOCAL_ENV%\\python.exe"
set "TCL_LIBRARY=%LOCAL_ENV%\\tcl8.6"
set "TK_LIBRARY=%LOCAL_ENV%\\tk8.6"
start "" "!PYTHON_EXEC!" "%SCRIPT_DIR%!TARGET_SCRIPT!"
exit /b 0

:end
exit /b

:log
echo %*
echo %* >> "%LOGFILE%"
goto :eof

:logOnly
echo %* >> "%LOGFILE%"
goto :eof
