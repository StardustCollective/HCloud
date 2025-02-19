#!/bin/bash
###############################################################################
# HCloud_Launcher.sh
#
# PURPOSE:
#   1) Check if Python >= 3.13.2 is installed. If not (or if only a stub is found),
#      prompt to install from python.org.
#   2) After installing/updating Python, install certificates if needed.
#   3) Check if dependencies (paramiko, cryptography, packaging, requests)
#      are installed; install only missing ones.
#   4) Ask user if they want to launch HCloud. If yes, check for HCloud.py locally;
#      if missing, download it from GitHub. Then run HCloud.py.
#
# This script:
#   - Uses the system Python directly.
#   - Installs pip packages system-wide (requires user permission or sudo).
#
# NOTE:
#   - macOS Gatekeeper: The user must chmod +x this script and possibly right-click → Open it.
#   - Installing Python from .pkg requires an admin password.
#
###############################################################################

ESC="$(printf '\033')"
BOLD="${ESC}[1m"
RESET="${ESC}[0m"
GREEN="${ESC}[1;32m"
YELLOW="${ESC}[1;33m"
RED="${ESC}[1;31m"
CYAN="${ESC}[1;36m"
BLUE="${ESC}[1;34m"

LOGFILE="$(pwd)/HCloud_launcher.log"

function log() {
  echo "$*" | tee -a "$LOGFILE"
}

function logOnly() {
  echo "$*" >> "$LOGFILE"
}

cd "$(dirname "$0")"

if [ -f "$LOGFILE" ]; then
  rm "$LOGFILE"
fi
logOnly "Starting HCloud launcher..."
logOnly "Log file location: $LOGFILE"

if [[ "$(uname -s)" != "Darwin" ]]; then
  log "Error: This script is intended for macOS only."
  exit 1
fi

echo "${BOLD}${BLUE}-----===[ HCloud Graphical User Interface ]===-----${RESET}"
echo "${GREEN}Brought to you by Techware - Developed by @Proph151Music${RESET}"
echo
echo "HCloud uses a secure setup that installs only what's needed to run HCloud."
echo "It can be removed at any time."
echo

function python_version_ok() {
  local py_cmd="$1"
  if [ -z "$py_cmd" ]; then
    return 1
  fi
  local ver
  ver=$("$py_cmd" -c 'import sys; v=sys.version_info; print(f"{v.major}.{v.minor}.{v.micro}")' 2>/dev/null)
  if [ -z "$ver" ]; then
    return 1
  fi

  local required="3.13.2"

  function ver_to_int() {
    local major minor micro
    IFS='.' read -r major minor micro <<< "$1"
    printf "%d%02d%02d" "$major" "$minor" "$micro"
  }

  local actual_int
  local required_int
  actual_int=$(ver_to_int "$ver")
  required_int=$(ver_to_int "$required")

  (( actual_int >= required_int ))
}

sys_python="$(command -v python3 || true)"
INSTALL_PYTHON=false

if [ -z "$sys_python" ]; then
  INSTALL_PYTHON=true
elif [ "$sys_python" = "/usr/bin/python3" ]; then
  if [ -f "/Applications/Xcode.app/Contents/Developer/usr/bin/python3" ]; then
    sys_python="/Applications/Xcode.app/Contents/Developer/usr/bin/python3"
  else
    INSTALL_PYTHON=true
  fi
fi

if ! $INSTALL_PYTHON; then
  if ! python_version_ok "$sys_python"; then
    log "Python found at: $sys_python but its version is lower than 3.13.2."
    INSTALL_PYTHON=true
  fi
fi

if $INSTALL_PYTHON; then
  log "A suitable Python (>=3.13.2) was NOT found or a stub version is in use."
  echo
  echo "${BOLD}${BLUE}We can automatically download & install Python 3.13.2 from python.org.${RESET}"
  echo "This step requires an admin password. The installer is ~25MB."
  read -p "Proceed with Python 3.13.2 installation? (Y/N): " installChoice
  case "$installChoice" in
    [Yy]* )
      log "User chose to install Python 3.13.2 from python.org."
      PKG_URL="https://www.python.org/ftp/python/3.13.2/python-3.13.2-macos11.pkg"
      PKG_FILE="python-3.13.2-macos11.pkg"
      log "Downloading $PKG_URL ..."
      curl -L -o "$PKG_FILE" "$PKG_URL" >> "$LOGFILE" 2>&1
      if [ $? -ne 0 ] || [ ! -f "$PKG_FILE" ]; then
        echo "${RED}Failed to download Python installer.${RESET}"
        log "Failed to download $PKG_URL"
        exit 1
      fi
      log "Installing Python 3.13.2..."
      sudo installer -pkg "$PKG_FILE" -target / >> "$LOGFILE" 2>&1
      if [ $? -ne 0 ]; then
        echo "${RED}Installation of Python 3.13.2 failed.${RESET}"
        logOnly "Installation of Python 3.13.2 failed."
        rm -f "$PKG_FILE"
        exit 1
      fi
      rm -f "$PKG_FILE"
      log "Python 3.13.2 installed successfully."

      sys_python="$(command -v python3 || true)"
      if python_version_ok "$sys_python"; then
        PY_CMD="$sys_python"
        echo "${GREEN}Python 3.13.2 is now installed.${RESET}"
      else
        echo "${RED}Could not verify Python 3.13.2 after install. Exiting.${RESET}"
        log "Python 3.13.2 post-install check failed."
        exit 1
      fi
      ;;
    * )
      echo
      echo "${RED}User declined Python installation. Exiting.${RESET}"
      log "User declined Python installation. Cannot proceed."
      exit 1
      ;;
  esac
else
  log "Python >= 3.13.2 found at: $sys_python"
  PY_CMD="$sys_python"
fi

CERT_INSTALLER="/Applications/Python 3.13/Install Certificates.command"
if [ -f "$CERT_INSTALLER" ]; then
  log "Found certificate installer at $CERT_INSTALLER. Running it..."
  bash "$CERT_INSTALLER" >> "$LOGFILE" 2>&1
  log "Certificates installed."
else
  log "Certificate installer not found; skipping certificate installation."
fi

echo
echo "${BOLD}Checking pip installation...${RESET}"
"$PY_CMD" -m pip --version >> "$LOGFILE" 2>&1
if [ $? -ne 0 ]; then
  log "pip not found. Installing with ensurepip..."
  "$PY_CMD" -m ensurepip --upgrade >> "$LOGFILE" 2>&1
  if [ $? -ne 0 ]; then
    echo "${RED}Failed to install pip. Check the log for details.${RESET}"
    exit 1
  fi
fi

logOnly "Upgrading pip..."
"$PY_CMD" -m pip install --upgrade pip >> "$LOGFILE" 2>&1
if [ $? -ne 0 ]; then
  echo "${RED}Failed to upgrade pip. Check the log for details.${RESET}"
  exit 1
fi
logOnly "pip is set up and upgraded."

REQ_PKGS=("paramiko" "cryptography" "packaging" "requests")

function package_installed() {
  local pkg="$1"
  "$PY_CMD" -c "import $pkg" 2>/dev/null
  return $?
}

echo
log "Checking required packages..."

for pkg in "${REQ_PKGS[@]}"; do
  if package_installed "$pkg"; then
    logOnly "$pkg is already installed. Skipping."
  else
    log "$pkg not found. Installing..."
    "$PY_CMD" -m pip install "$pkg" >> "$LOGFILE" 2>&1
    if [ $? -ne 0 ]; then
      echo "${RED}Failed to install package: $pkg${RESET}"
      log "Failed installing $pkg"
      exit 1
    else
      log "$pkg installed successfully."
    fi
  fi
done

logOnly "All required packages are installed."
clear

echo
echo "${BOLD}${BLUE}==========================================================================${RESET}"
echo "${BOLD}${BLUE}             Welcome to the HCloud Graphical User Interface${RESET}"
echo "${BOLD}                Developed by: @Proph151Music of Techware${RESET}"
echo "${BOLD}${BLUE}==========================================================================${RESET}"
echo
echo "${BOLD}HCloud GUI is designed to make setting up your DAG Validator Node a breeze.${RESET}"
echo
echo " - Quickly create a cloud server on Hetzner"
echo " - Easily install and configure nodectl"
echo
echo "This secure setup installs everything in your system Python (or newly installed"
echo "Python 3.13.2), ensuring that your computer settings remain stable."
echo
echo "${BOLD}If you find HCloud helpful and you are feeling generous, consider sending a tip."
echo "You can donate${RED} ${BOLD}\$DAG, \$PACA, \$DOR or any Metagraph tokens${RESET}${BOLD} to the wallet below:${RESET}"
echo
echo "${BOLD}${BLUE}               DAG0Zyq8XPnDKRB3wZaFcFHjL4seCLSDtHbUcYq3${RESET}"
echo

read -p "Do you want to download and launch the latest version of the Hetzner Cloud Management Tool (HCloud)? (Y/N): " runChoice 
case "$runChoice" in
  [Yy]* )
    tempFile=$(mktemp /tmp/HCloud.XXXXXX.py)
    log "Downloading HCloud.py to temporary file..."
    
    curl -L -o "$tempFile" "https://raw.githubusercontent.com/Proph151Music/HCloud/main/HCloud.py" >> "$LOGFILE" 2>&1
    if [ $? -ne 0 ] || [ ! -f "$tempFile" ]; then
      echo "${RED}Failed to download HCloud.py.${RESET}"
      log "Failed to download HCloud.py"
      exit 1
    else
      log "HCloud.py downloaded successfully to temporary file."
      mv -f "$tempFile" "HCloud.py"
    fi

    log "Launching HCloud.py with: $PY_CMD"
    nohup "$PY_CMD" "HCloud.py" >/dev/null 2>&1 &
    exit 0
    ;;
  * )
    echo
    echo "${RED}Launch canceled by user. Exiting.${RESET}"
    log "User declined to launch HCloud."
    exit 0
    ;;
esac
