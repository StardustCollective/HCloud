@echo off
REM ========================================================
REM Portable HCloud Launcher
REM This batch file creates a portable local_env (using Python embeddable),
REM configures the local environment by enabling the standard library,
REM Scripts, Lib, and DLLs folders via the python313._pth file,
REM downloads tcl.zip from GitHub and extracts Tcl/Tk (for tkinter),
REM upgrades pip and installs required packages (paramiko, cryptography,
REM packaging, pywin32), and finally offers to launch HCloud.py.
REM ========================================================

for /F "delims=" %%A in ('echo prompt $E^|cmd') do set "ESC=%%A"
set "BOLD=%ESC%[1m"
set "BLUE=%ESC%[1;34m"
set "CYAN=%ESC%[1;36m"
set "MAGENTA=%ESC%[1;35m"
set "RESET=%ESC%[0m"
set "GREEN=%ESC%[1;32m"
set "YELLOW=%ESC%[1;33m"
set "RED=%ESC%[1;31m"

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "LOGFILE=%SCRIPT_DIR%HCloud_launcher.log"
if exist "%LOGFILE%" del "%LOGFILE%"

call :logOnly "Log file location: %LOGFILE%"
call :logOnly "Starting HCloud launcher..."

net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
setlocal enabledelayedexpansion

set "LOCAL_ENV=%SCRIPT_DIR%local_env"

if exist "%LOCAL_ENV%" (
    call :logOnly "Portable Python Environment detected. Skipping installation steps."
    goto check_and_run_HCloud
)

echo.
echo %BOLD%%YELLOW%-----===[ HCloud Graphical User Interface]===-----%RESET%
echo %GREEN%Brought to you by Techware - Developed by @Proph151Music%RESET%
echo.
echo HCloud uses a secure, self-contained setup that installs everything in its own folder.
echo This process will not change your system settings and can be removed at any time.
echo.
set /p setupChoice="Do you want to set up a local environment for HCloud? (Y/N): "
if /I "!setupChoice!"=="Y" (
    call :log User agreed to set up the portable environment. Proceeding with installation...
) else (
    echo.
    echo %RED%Setup canceled by user. Exiting.%RESET%
    pause
    exit /b
)

call :log Downloading Python embeddable from https://www.python.org/ftp/python/3.13.2/python-3.13.2-embed-amd64.zip...
set "ZIP_PATH=%TEMP%\python-embed.zip"
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.2/python-3.13.2-embed-amd64.zip' -OutFile '!ZIP_PATH!'" >> "%LOGFILE%" 2>&1
if exist "!ZIP_PATH!" (
    call :log Download succeeded. Extracting...
    powershell -NoProfile -Command "Expand-Archive -Path '!ZIP_PATH!' -DestinationPath '!LOCAL_ENV!' -Force" >> "%LOGFILE%" 2>&1
    if errorlevel 1 (
        call :log ERROR: Extraction failed!
        exit /b 1
    ) else (
        call :log Extraction complete.
    )
    del "!ZIP_PATH!"
) else (
    call :log ERROR: Failed to download Python embeddable!
    exit /b 1
)

if exist "%LOCAL_ENV%\python313._pth" (
    call :log Configuring portable Python environment...
    powershell -NoProfile -Command "(Get-Content '%LOCAL_ENV%\python313._pth') -replace '^#\s*import site', 'import site' | Set-Content '%LOCAL_ENV%\python313._pth'" >> "%LOGFILE%" 2>&1
    powershell -NoProfile -Command "if (-not (Select-String -Path '%LOCAL_ENV%\python313._pth' -Pattern '^Scripts$')) { Add-Content -Path '%LOCAL_ENV%\python313._pth' -Value 'Scripts' }" >> "%LOGFILE%" 2>&1
    powershell -NoProfile -Command "if (-not (Select-String -Path '%LOCAL_ENV%\python313._pth' -Pattern '^Lib$')) { Add-Content -Path '%LOCAL_ENV%\python313._pth' -Value 'Lib' }" >> "%LOGFILE%" 2>&1
    powershell -NoProfile -Command "if (-not (Select-String -Path '%LOCAL_ENV%\python313._pth' -Pattern '^DLLs$')) { Add-Content -Path '%LOCAL_ENV%\python313._pth' -Value 'DLLs' }" >> "%LOGFILE%" 2>&1
) else (
    call :log Warning: python313._pth not found in local_env.
)

set "TCL_ZIP_PATH=%SCRIPT_DIR%tcl.zip"
set "TCL_GITHUB_URL=https://github.com/StardustCollective/HCloud/raw/main/Windows/tcl.zip"
if not exist "%TCL_ZIP_PATH%" (
    call :log Tcl/Tk archive not found locally. Downloading from GitHub...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri '!TCL_GITHUB_URL!' -OutFile '!TCL_ZIP_PATH!'" >> "%LOGFILE%" 2>&1
    if not exist "%TCL_ZIP_PATH%" (
        call :log ERROR: Failed to download tcl.zip from GitHub!
        exit /b 1
    )
)
call :log Extracting Tcl/Tk from tcl.zip...
powershell -NoProfile -Command "Expand-Archive -Path '%TCL_ZIP_PATH%' -DestinationPath '%LOCAL_ENV%' -Force" >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    call :log ERROR: Extraction of Tcl/Tk failed!
    exit /b 1
) else (
    call :log Tcl/Tk successfully extracted.
)
del "%TCL_ZIP_PATH%"

if not exist "%LOCAL_ENV%\python.exe" (
    call :log ERROR: python.exe not found in local_env!
    exit /b 1
)

call :log Checking for pip...
"%LOCAL_ENV%\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 (
    call :log pip not found. Installing pip via get-pip.py...
    set "GET_PIP_PATH=%TEMP%\get-pip.py"
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '!GET_PIP_PATH!'" >> "%LOGFILE%" 2>&1
    if exist "!GET_PIP_PATH!" (
        call :log Running get-pip.py...
        "%LOCAL_ENV%\python.exe" "!GET_PIP_PATH!" >> "%LOGFILE%" 2>&1
        if errorlevel 1 (
            call :log ERROR: Failed to install pip!
            exit /b 1
        ) else (
            call :log pip installed successfully.
            ECHO.
        )
        del "!GET_PIP_PATH!"
    ) else (
        call :log ERROR: Failed to download get-pip.py!
        exit /b 1
    )
) else (
    ECHO.
)

call :log Upgrading pip...
"%LOCAL_ENV%\python.exe" -m pip install --upgrade pip >> "%LOGFILE%" 2>&1

call :log Installing required packages: paramiko, cryptography, packaging, pywin32...
"%LOCAL_ENV%\python.exe" -m pip install paramiko cryptography packaging pywin32 >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    call :log ERROR: Failed to install one or more required packages!
    exit /b 1
) else (
    call :log All required packages installed successfully.
    ECHO.
)

:check_and_run_HCloud
SET "HCLOUD_FILE=HCloud.py"
SET "DOWNLOAD_URL=https://raw.githubusercontent.com/StardustCollective/HCloud/main/HCloud.py"

echo %BOLD%%GREEN%==========================================================================%RESET%
echo %BOLD%%GREEN%             Welcome to the HCloud Graphical User Interface%RESET%
echo %BOLD%%CYAN%                Developed by: @Proph151Music of Techware%RESET%
echo %BOLD%%GREEN%==========================================================================%RESET%
echo.
echo %BOLD%HCloud GUI is designed to make setting up your DAG Validator Node a breeze.%RESET%
echo.
echo  - Quickly create a cloud server on Hetzner
echo  - Easily install and configure nodectl
echo.
echo This secure, self-contained setup installs everything in its own folder,
echo ensuring that your computer settings remain untouched.
echo.
echo %BLUE%If you find HCloud helpful and you are feeling generous, consider sending a tip.
echo You can donate%RESET% %BOLD%$DAG, $PACA, $DOR or any Metagraph tokens%RESET%%BLUE% to the wallet below:%RESET%
echo %BOLD%%YELLOW%               DAG0Zyq8XPnDKRB3wZaFcFHjL4seCLSDtHbUcYq3%RESET%
echo.
echo.
echo %BOLD%%GREEN% The HCloud Portal Awaits You...%RESET%

IF EXIST "%HCLOUD_FILE%" (
    ECHO [D] - Download and Launch HCloud
    ECHO [L] - Launch the local copy of HCloud
    ECHO [C] - Cancel
    ECHO.
    CHOICE /C DLC /N /M "Enter your choice (D, L, or C): "
    IF ERRORLEVEL 3 GOTO :end
    IF ERRORLEVEL 2 GOTO :LAUNCH
    IF ERRORLEVEL 1 GOTO :DOWNLOAD
) ELSE (
    ECHO.
    ECHO [D] Download and Launch HCloud
    ECHO [C] Cancel
    ECHO.
    CHOICE /C DC /N /M "Enter your choice (D or C): "
    IF ERRORLEVEL 2 GOTO :end
    IF ERRORLEVEL 1 GOTO :DOWNLOAD
)

:DOWNLOAD
ECHO.
call :log Downloading latest version of %HCLOUD_FILE%...
SET "TEMP_FILE=%HCLOUD_FILE%.tmp"
IF EXIST "%TEMP_FILE%" DEL /Q "%TEMP_FILE%"
PowerShell -Command "Try {Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%TEMP_FILE%'; Exit 0} Catch {Exit 1}"
IF %ERRORLEVEL% NEQ 0 (
    call :log Download failed. Keeping existing file.
    GOTO :end
)
MOVE /Y "%TEMP_FILE%" "%HCLOUD_FILE%" >NUL
call :log Download complete. Launching latest version...
GOTO :LAUNCH

:LAUNCH
ECHO.
if exist "%LOCAL_ENV%\pythonw.exe" (
    set "PYTHON_EXEC=%LOCAL_ENV%\pythonw.exe"
) else if exist "%LOCAL_ENV%\python.exe" (
    set "PYTHON_EXEC=%LOCAL_ENV%\python.exe"
) else (
    call :log ERROR: Python executable not found in portable environment!
    pause
    exit /b
)
call :log Launching HCloud.py from directory: %cd%
call :log Running HCloud.py using !PYTHON_EXEC! %SCRIPT_DIR%HCloud.py
set "TCL_LIBRARY=%LOCAL_ENV%\tcl8.6"
set "TK_LIBRARY=%LOCAL_ENV%\tk8.6"
start "" "!PYTHON_EXEC!" "%SCRIPT_DIR%HCloud.py"
exit /b 0

:end
exit /b

:log
echo %*
echo %* >> "%LOGFILE%"
goto :eof

:log
echo %*
echo %* >> "%LOGFILE%"
goto :eof

:logOnly
echo %* >> "%LOGFILE%"
goto :eof
