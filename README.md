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
  - [MacOS](#macos)
  - [Ubuntu Desktop](#ubuntu-desktop)
  - [ChromeOS](#chromeos)
    
- [How to Use HCloud](#how-to-use-hcloud)
  - [Launch HCloud](#launch-hcloud)
  - [Enter Your Hetzner API Key](#enter-your-hetzner-api-key)
  - [Create Server Tab](#create-server-tab)
  - [Install nodectl Tab](#install-nodectl-tab)
- [Import Server Settings Into Termius](#import-server-settings-into-termius)
  
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

### MacOS

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

### Launch HCloud

1. **Launch `HCloud_Launcher.bat` (Windows) or `HCloud_Launcher.sh` (MacOS):**
   - Do you want to set up a local environment for HCloud?
     -----
     <img width="489" alt="image" src="https://github.com/user-attachments/assets/dcaee374-87e4-4332-ae90-52d5af9fabe4" />
     
     Send `Y` for Yes. This will download Python and install all of the needed dependencies for HCloud. this is only needed the first time you use HCloud.
     
   - At the next step you will be asked how you want to Launch HCloud.
     -----
     <img width="460" alt="image" src="https://github.com/user-attachments/assets/49881c69-fe90-429c-ab95-54da5d6a2370" />
     
     If this is the first launch, you will need to send `d` for Download. In the future you can send `D` to download the latest version or `L` to launch the current version you have.
     
-----

2. #### Enter Your Hetzner API Key
   - When prompted, paste your Hetzner Cloud API key.
     -----
   ![Screenshot 2025-02-19 162320](https://github.com/user-attachments/assets/5624a3f6-5aa5-4dac-84a0-34426ffaf5fe)

     If you don’t have one, follow these steps:
   
     -----
   **Creating a Hetzner API Key:**
   - **Log in to Hetzner Cloud:**  
     Visit the [Hetzner Cloud Console](https://console.hetzner.cloud) and sign in.
   - **Navigate to API Settings:**  
     Click **Security > API Tokens** in the left-hand menu.
   - **Generate a New API Key:**
     - Click **Generate API Token**.
       
       <img width="395" alt="image" src="https://github.com/user-attachments/assets/3fca9109-e372-4fd4-ab96-9c960ba11cd2" />

     - Enter a name (e.g., "HCloud GUI") and select **Read/Write permissions**.
     - Click **Generate API token**.
   - **Copy Your API Key:**
  
     <img width="401" alt="image" src="https://github.com/user-attachments/assets/a538141d-0356-4df8-a9a3-51110b485b03" />

     Since the key is shown only once, copy it now and paste it into HCloud. For security purposes it is not recommended to save this API key anywhere. You can always create a new one later if you need one in the future.
     
     -----
     
3. **Manage Your Cloud Resources:**

   ### Create Server Tab

   <img width="611" alt="image" src="https://github.com/user-attachments/assets/7d75d9b0-38e0-4ca7-b947-a0edc8c8afb5" />

     Enter a Server Name, select a Location, choose the Server Specs and the Distribution OS.  
     HCloud auto-fills firewall and SSH key names if you leave them blank.
   
     -----
     
  - Click the `Create Server` button once you have entered all of the needed information.
    
     - **Firewall Management:**  
       You’ll be prompted to add your Home IP for extra security. (This helps prevent unauthorized access.)
       ![Screenshot 2025-02-24 140735 copy](https://github.com/user-attachments/assets/36ac43cb-400b-4c79-bbeb-7fb81d228afd)

         If you choose `Yes` then HCloud will ask if you have additional IP addresses you would like to give access to this server. For instance a Mobile Data IP address or maybe a Work IP. You can find the correct IP's by making sure you browse to whatsmyip.org on a device connected to that network.
       
       <img width="297" alt="image" src="https://github.com/user-attachments/assets/cc0be20b-1e4a-4fcb-9a41-de1032d4fe1d" />

       <img width="478" alt="image" src="https://github.com/user-attachments/assets/73674df2-959d-4cfb-8544-f99fd62e5dd3" />

       -----
       
     - **SSH Key Management:**  
       Import or create new SSH key pairs directly within HCloud.  
       You’ll be asked to create a passphrase for any new ssh keys.
       
       <img width="257" alt="image" src="https://github.com/user-attachments/assets/02802355-4814-4b0f-8a7f-a2d5358a1aa9" />
       
       Be sure to document any new passwords! HCloud does not save this information for you.  It is your responsibility to remember any passwords you create.
       
       -----

      Once the server is created you will see the `Success` window pop up.
    
      <img width="298" alt="image" src="https://github.com/user-attachments/assets/2619f58e-1955-42ce-901a-c95e353041f7" />
      
      If you get a message about "Resource not available" then you need to choose different specs or change the location and try again. This is usually an indication that the specs you selected are sold out at that location.

       
   ### Install nodectl Tab

   <img width="614" alt="image" src="https://github.com/user-attachments/assets/cc192359-f107-4acf-ac84-90e5d120955b" />

   - **Select Server & Network:**  
     Your server details and network selection are auto-populated after server creation.
   - **Node Username:**  
     Defaults to `nodeadmin` (change if needed, but remember it).
   - **nodectl Version:**  
     Make sure you install the correct nodectl version (check your Discord chat for details).
   - **Additional Options:**  
     - **Import P12 File (Optional):** Import your P12 file if you are rebuilding a node.
     - **Desktop Shortcuts:** On Windows, you can choose to create SSH/SFTP shortcuts.
     - **Export to PuTTY:** (Windows Only) If you have PuTTY and WinSCP installed, HCloud can export server settings to PuTTY.

---

## Import Server Settings Into Termius

   After you have successfully installed nodectl on your new cloud server, you can easily import the server settings into Termius.

   - **Open Termius on your Windows or MacOS**
   - Click the dropdown on `New Host` and select `Import`.

     ![Screenshot 2025-02-24 163041](https://github.com/user-attachments/assets/44154962-1683-4d87-af4c-60a297f331b3)

   - Select option ssh_config (Windows) or SSH:> (MacOS).

     <img width="399" alt="image" src="https://github.com/user-attachments/assets/b428a9ad-3973-44a5-994b-17df2315dceb" />

   - On Windows you will browse to your config file that was created by HCloud. It can be found next to the HCloud files inside of a folder named `SERVERS`.
   - On MacOS you do not need to browse. You should see the details already available to submit.

     -----
     
## Acknowledgments

This tool was created by `@Proph151Music` for the Constellation Network ecosystem.  
If you find HCloud helpful, please consider sending a tip!

**DAG Wallet Address:**  
`DAG0Zyq8XPnDKRB3wZaFcFHjL4seCLSDtHbUcYq3`

---

Enjoy managing your Hetzner Cloud Server with **HCloud**!
