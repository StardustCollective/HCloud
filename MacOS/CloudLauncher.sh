#!/bin/bash

ESC="$(printf '\033')"
BOLD="${ESC}[1m"
RESET="${ESC}[0m"
GREEN="${ESC}[1;32m"
YELLOW="${ESC}[1;33m"
RED="${ESC}[1;31m"
CYAN="${ESC}[1;36m"
BLUE="${ESC}[1;34m"

LOGFILE="$(pwd)/CloudLauncher.log"

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
logOnly "Starting CloudLauncher..."
logOnly "Log file location: $LOGFILE"

if [[ "$(uname -s)" != "Darwin" ]]; then
  log "Error: This script is intended for macOS only."
  exit 1
fi

function python_version_ok() {
  local py_cmd="$1"
  if [ -z "$py_cmd" ]; then return 1; fi
  local ver
  ver=$("$py_cmd" -c 'import sys; v=sys.version_info; print(f"{v.major}.{v.minor}.{v.micro}")' 2>/dev/null)
  if [ -z "$ver" ]; then return 1; fi
  local required="3.13.2"

  function ver_to_int() {
    local major minor micro
    IFS='.' read -r major minor micro <<< "$1"
    printf "%d%02d%02d" "$major" "$minor" "$micro"
  }

  local actual_int required_int
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
      curl -L -o "$PKG_FILE" "$PKG_URL" >> "$LOGFILE" 2>&1
      sudo installer -pkg "$PKG_FILE" -target / >> "$LOGFILE" 2>&1
      rm -f "$PKG_FILE"
      hash -r
      sys_python="$(command -v python3 || true)"
      if python_version_ok "$sys_python"; then
        PY_CMD="$sys_python"
        echo "${GREEN}Python 3.13.2 is now installed.${RESET}"
      else
        echo "${RED}Python installation failed verification. Exiting.${RESET}"
        exit 1
      fi
      ;;
    * )
      echo "${RED}User declined Python installation. Exiting.${RESET}"
      exit 1
      ;;
  esac
else
  PY_CMD="$sys_python"
  log "Python >= 3.13.2 found at: $PY_CMD"
fi

CERT_INSTALLER="/Applications/Python 3.13/Install Certificates.command"
if [ -f "$CERT_INSTALLER" ]; then
  log "Found certificate installer at $CERT_INSTALLER. Running it..."
  bash "$CERT_INSTALLER" >> "$LOGFILE" 2>&1
  log "Certificates installed."
fi

"$PY_CMD" -m pip --version >> "$LOGFILE" 2>&1 || "$PY_CMD" -m ensurepip --upgrade >> "$LOGFILE" 2>&1
"$PY_CMD" -m pip install --upgrade pip >> "$LOGFILE" 2>&1

REQ_PKGS=("requests" "paramiko" "cryptography" "packaging" "pywin32")

function package_installed() {
  "$PY_CMD" -c "import $1" 2>/dev/null
}

log "Checking required packages..."
for pkg in "${REQ_PKGS[@]}"; do
  if ! package_installed "$pkg"; then
    log "$pkg not found. Installing..."
    "$PY_CMD" -m pip install "$pkg" >> "$LOGFILE" 2>&1
  fi
done

clear
echo
echo "${BOLD}${BLUE}==========================================================================${RESET}"
echo "${BOLD}${BLUE}           Welcome to the Cloud Deployment Launcher (macOS)${RESET}"
echo "${BOLD}            Developed by: @Proph151Music of Techware${RESET}"
echo "${BOLD}${BLUE}==========================================================================${RESET}"
echo
echo "${BOLD}Choose your cloud platform below.${RESET}"
echo "All dependencies have been installed and are ready to go."
echo
echo "If this project helped you, consider tipping:"
echo "${BOLD}${YELLOW}DAG0Zyq8XPnDKRB3wZaFcFHjL4seCLSDtHbUcYq3${RESET}"
echo

echo "[1] Launch Hetzner (HCloud)"
echo "[2] Launch DigitalOcean (DOCloud)"
read -p "Enter your choice [1-2]: " provider_choice

if [[ "$provider_choice" == "1" ]]; then
  TARGET_NAME="HCloud"
  TARGET_URL="https://raw.githubusercontent.com/StardustCollective/HCloud/main/HCloud.py"
elif [[ "$provider_choice" == "2" ]]; then
  TARGET_NAME="DOCloud"
  TARGET_URL="https://raw.githubusercontent.com/StardustCollective/HCloud/main/DOCloud.py"
else
  echo "${RED}Invalid selection. Exiting.${RESET}"
  exit 1
fi

echo
echo "[D] Download and launch latest $TARGET_NAME"
echo "[L] Launch local $TARGET_NAME.py"
echo "[C] Cancel"
read -p "Enter your choice (D/L/C): " action_choice

case "$action_choice" in
  [Dd]* )
    TMP_PY=$(mktemp /tmp/${TARGET_NAME}.XXXXXX.py)
    curl -L -o "$TMP_PY" "$TARGET_URL" >> "$LOGFILE" 2>&1
    mv -f "$TMP_PY" "${TARGET_NAME}.py"
    nohup "$PY_CMD" "${TARGET_NAME}.py" >/dev/null 2>&1 &
    ;;
  [Ll]* )
    nohup "$PY_CMD" "${TARGET_NAME}.py" >/dev/null 2>&1 &
    ;;
  * )
    echo "${RED}Cancelled by user. Exiting.${RESET}"
    exit 0
    ;;
esac
