# HCloud - Hetzner Cloud Management GUI

This tool is currently in beta!  
If you use it, please report any issues to `@Proph151Music`.  
The script will be updated soon with improvements based on user feedback.

Don't forget to tip the bartender!

**DAG Wallet Address for sending tips:**  
`DAG0Zyq8XPnDKRB3wZaFcFHjL4seCLSDtHbUcYq3`

---

Welcome to **HCloud**, a user-friendly GUI tool for managing your Hetzner Cloud infrastructure. Whether you're creating servers, setting up firewalls, managing SSH keys, or installing nodectl, HCloud streamlines these tasks so you don’t have to be a tech expert.

## Key Features

- **Manage Servers:** Easily create, view, and delete servers.
- **Firewall Management:** Quickly set up and edit firewall rules.
- **SSH Key Management:** Import or create SSH keys for secure access.
- **Install nodectl:** Install nodectl on your servers with minimal effort.
- **Cross-platform Support:** Runs on Windows, macOS, Ubuntu Desktop, and ChromeOS.

## Table of Contents

- [Installation](#installation)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Ubuntu Desktop](#ubuntu-desktop)
  - [ChromeOS](#chromos)
- [How to Use HCloud](#how-to-use-hcloud)
  - [Enter Your Hetzner API Key](#enter-your-hetzner-api-key)
- [Acknowledgments](#acknowledgments)

---

## Installation

### Windows

**Download and Extract the HCloud_launcher.zip file**

1. **Download the File:**
   - [Right-click here and select "Save As"](https://github.com/StardustCollective/HCloud/raw/main/Windows/HCloud_Launcher.zip) to download the `HCloud_launcher.zip` file.
   - Save it to your desired location (e.g., `C:\Users\YourUsername\Downloads`).

2. **Extract the File:**
   - Right-click on the ZIP file and choose "Extract All..."
   - Select your extraction folder and click "Extract".

3. **Run the File:**
   - Open the extracted folder and double-click `HCloud_launcher.bat` to run it.

---

### macOS

Open **Terminal** and run:

```bash
curl -L -O https://raw.githubusercontent.com/StardustCollective/HCloud/main/MacOS/HCloud_Launcher.sh && chmod +x HCloud_Launcher.sh && ./HCloud_Launcher.sh
```

---

### Ubuntu Desktop

Open **Terminal** and run:

```bash
wget https://raw.githubusercontent.com/StardustCollective/HCloud/main/HCloud.py && python3 HCloud.py
```

---

### ChromeOS

If Linux is enabled on your ChromeOS device, open the **Linux terminal** and run:

```bash
wget https://raw.githubusercontent.com/StardustCollective/HCloud/main/HCloud.py && python3 HCloud.py
```

---

## How to Use HCloud

1. **Launch HCloud:**  
   Follow the installation steps for your OS. When HCloud starts, you'll see a simple GUI.

2. **Enter Your Hetzner API Key:**  
   When prompted, paste your Hetzner Cloud API key. If you don’t have one, follow these steps:

   **Creating a Hetzner API Key:**
   - **Log in to Hetzner Cloud:**  
     Visit the [Hetzner Cloud Console](https://console.hetzner.cloud) and sign in.
   - **Navigate to API Settings:**  
     Click **Security > API Tokens** in the left-hand menu.
   - **Generate a New API Key:**
     - Click **Generate API Token**.
     - Enter a name (e.g., "HCloud GUI") and select **Read/Write permissions**.
     - Click **Generate Token**.
   - **Copy Your API Key:**  
     Since the key is shown only once, copy it now and paste it into HCloud.

3. **Manage Your Cloud Resources:**

   ### Create Server Tab
   - **Create New Servers:**  
     Enter a server name, select a location and distribution.  
     HCloud auto-fills firewall and SSH key names if you leave them blank.
   - **Firewall Management:**  
     You’ll be prompted to add your Home IP for extra security. (This helps prevent unauthorized access.)
   - **SSH Key Management:**  
     Import or create new SSH key pairs directly within HCloud.  
     You’ll be asked to set a passphrase for new keys—be sure to document it carefully!
     
   ### Install nodectl Tab
   - **Select Server & Network:**  
     Your server details and network selection are auto-populated after server creation.
   - **Node Username:**  
     Defaults to `nodeadmin` (change if needed, but remember it).
   - **nodectl Version:**  
     Make sure you install the correct nodectl version (check your Discord chat for details).
   - **Additional Options:**  
     - **Import P12 File (Optional):** Import your P12 file if you are rebuilding a node.
     - **Desktop Shortcuts:** On Windows, you can choose to create SSH/SFTP shortcuts; on macOS/Linux, aliases may be created.
     - **Export to PuTTY:** (Windows Only) If you have PuTTY and WinSCP installed, HCloud can export server settings to PuTTY.

---

## Acknowledgments

This tool was created by `@Proph151Music` for the Constellation Network ecosystem.  
If you find HCloud helpful, please consider sending a tip!

**DAG Wallet Address:**  
`DAG0Zyq8XPnDKRB3wZaFcFHjL4seCLSDtHbUcYq3`

---

Enjoy managing your Hetzner Cloud with **HCloud**!
