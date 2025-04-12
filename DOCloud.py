import os
import subprocess
import sys
import platform
import re
import logging
import urllib.request
import queue
import threading
import time
import ipaddress
import webbrowser
import shlex
import csv
import shutil
import json

# provider = os.getenv("CLOUD_PROVIDER", "digitalocean").lower()
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# Create a file handler which logs even debug messages
fh = logging.FileHandler("Debug.log", mode="w")
fh.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
fh.setFormatter(formatter)

# # Add the handler to the logger
# logger.addHandler(fh)


root = None
restart_required = False

# Ensure Python 3.13+ on macOS
def ensure_python_and_brew(log_widget=None):
    if platform.system() == "Darwin":
        python_version_output = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        ).stdout.strip()
        current_version = tuple(map(int, python_version_output.split()[1].split(".")))

        if current_version < (3, 13):
            if log_widget:
                log_widget.insert(tk.END, "Upgrading Python to 3.13+ with Homebrew...\n")
                log_widget.see(tk.END)

            try:
                subprocess.check_call(["brew", "install", "python@3.13"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                configure_brew_path()

                new_python_path = subprocess.check_output(["which", "python3.13"]).strip().decode()
                os.execv(new_python_path, ["python3.13"] + sys.argv)

            except subprocess.CalledProcessError as e:
                if log_widget:
                    log_widget.insert(tk.END, f"Failed to upgrade Python: {e}\n")
                    log_widget.see(tk.END)
                sys.exit(1)
        else:
            print(f"Python version is sufficient: {python_version_output}")

def configure_brew_path():
    """Ensure Homebrew is in the PATH for both zsh and bash users."""
    brew_path = "/opt/homebrew/bin"
    shell_profile = os.path.expanduser("~/.zshrc" if os.environ.get("SHELL", "").endswith("zsh") else "~/.bash_profile")
    
    if brew_path not in os.environ.get("PATH", ""):
        print(f"Adding {brew_path} to PATH in {shell_profile}...")
        with open(shell_profile, "a") as file:
            file.write(f'\n# Add Homebrew to PATH\nexport PATH="{brew_path}:$PATH"\n')
        
        subprocess.call(f"source {shell_profile}", shell=True)
        print("PATH updated and profile reloaded.")

ensure_python_and_brew()

def ensure_tkinter():
    """Ensure tkinter is available."""
    try:
        import tkinter as tk
        from tkinter import scrolledtext, ttk, messagebox, filedialog
        import tkinter.simpledialog as simpledialog
        import tkinter.font as tkFont
        # print("tkinter is available.")
    except ImportError:
        print("tkinter not found. Attempting to install...")
        if platform.system() == "Darwin":
            try:
                # Install Tcl/Tk and Python dependencies using Homebrew
                subprocess.check_call(["brew", "install", "tcl-tk"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.check_call(["brew", "reinstall", "python"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Update environment variables for Tcl/Tk
                os.environ["PATH"] = f"/opt/homebrew/opt/tcl-tk/bin:{os.environ.get('PATH', '')}"
                os.environ["LDFLAGS"] = "-L/opt/homebrew/opt/tcl-tk/lib"
                os.environ["CPPFLAGS"] = "-I/opt/homebrew/opt/tcl-tk/include"
                os.environ["PKG_CONFIG_PATH"] = "/opt/homebrew/opt/tcl-tk/lib/pkgconfig"

                # Verify tkinter installation
                try:
                    subprocess.check_call(["python3", "-m", "tkinter"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("tkinter is successfully installed.")
                except subprocess.CalledProcessError:
                    raise RuntimeError("Tkinter verification failed after installation.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install Tcl/Tk or tkinter: {e}")
                sys.exit(1)
        else:
            print("tkinter installation not automated for this OS. Please install it manually.")
            sys.exit(1)

ensure_tkinter()

import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk, messagebox, filedialog
import tkinter.simpledialog as simpledialog
import tkinter.font as tkFont

def requires_break_system_packages():
    try:
        output = subprocess.check_output(
            [sys.executable, "-m", "pip", "install", "--dry-run", "requests"],
            stderr=subprocess.STDOUT
        ).decode()
        return "externally-managed-environment" in output
    except subprocess.CalledProcessError as e:
        return False
    
if os.environ.get("RESTARTED") == "1":
    # Remove the environment variable to prevent infinite restarts
    del os.environ["RESTARTED"]
else:
    pass

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def install_package(package_name, log_widget=None):
    try:
        if log_widget:
            log_widget.insert(tk.END, f"Installing {package_name} package...\n")
            log_widget.see(tk.END)
        print(f"Installing {package_name}...")

        env = os.environ.copy()
        env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"

        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name], env=env)

        if log_widget:
            log_widget.insert(tk.END, f"Package {package_name} installed successfully.\n")
            log_widget.see(tk.END)
        print(f"Package {package_name} installed successfully.")

    except subprocess.CalledProcessError as e:
        if log_widget:
            log_widget.insert(tk.END, f"Failed to install package {package_name}: {e}\n")
            log_widget.see(tk.END)
        print(f"Failed to install package {package_name}: {e}")
        sys.exit(1)

def restart_script():
    try:
        global root
        if root is not None:
            messagebox.showinfo("Restart Required", "The script has finished installing dependencies. Please launch the script again to continue.")
            root.destroy()
            root.quit()
        else:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Restart Required", "The script has finished installing dependencies. Please launch the script again to continue.")
            root.destroy()

        os.environ["RESTARTED"] = "1"
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)

    except Exception as e:
        print(f"Failed to restart script: {e}")
        sys.exit(1)
        
def install_pywin32(log_widget=None):
    logging.debug("Checking if PyWin32 is installed...")
    if os.name == 'nt':
        try:
            import win32api
            if log_widget:
                log_widget.insert(tk.END, "PyWin32 is already installed.\n")
                log_widget.see(tk.END)
            logging.debug("PyWin32 is already installed.")
        except ImportError:
            logging.debug("PyWin32 not found. Installing PyWin32...")
            install_package('pywin32', log_widget)
            try:
                subprocess.check_call([sys.executable, '-m', 'pywin32_postinstall', 'install'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if log_widget:
                    log_widget.insert(tk.END, "PyWin32 post-installation completed.\n")
                    log_widget.see(tk.END)
                logging.debug("PyWin32 post-installation completed.")
                
                global restart_required
                restart_required = True

            except subprocess.CalledProcessError as e:
                if log_widget:
                    log_widget.insert(tk.END, f"Warning: Failed to run pywin32 post-installation: {e}\n")
                    log_widget.see(tk.END)
                logging.warning(f"Failed to run pywin32 post-installation: {e}")

def on_installation_complete(root, api_key):
    try:
        print("Installation complete. Hiding log window...")

        root.after(0, lambda: log_window.withdraw()) 

        print("Hiding root window...")
        root.after(0, lambda: root.withdraw())

        print("Creating application window...")
        root.after(0, lambda: create_app_window(api_key))
    except Exception as e:
        print(f"An error occurred in on_installation_complete: {e}")

def install_required_packages_in_thread(log_widget=None, completion_callback=None):
    def install_packages():
        ensure_python_and_brew(log_widget)
        install_required_packages(log_widget)
        if completion_callback:
            print("Calling completion_callback")
            completion_callback()

    thread = threading.Thread(target=install_packages)
    thread.daemon = True
    thread.start()

def install_required_packages(log_widget=None):
    global requests, paramiko
    required_packages = ["requests", "paramiko>=3.0.0", "cryptography>=39.0.0", "packaging"]
    for package in required_packages:
        package_name = package.split('>=')[0]
        logging.debug(f"Checking if package '{package_name}' is installed...")
        try:
            __import__(package_name)
            if log_widget:
                log_widget.insert(tk.END, f"Package '{package_name}' is already installed.\n")
                log_widget.see(tk.END)
            logging.debug(f"Package '{package_name}' is already installed.")
        except ImportError:
            if log_widget:
                log_widget.insert(tk.END, f"Installing package '{package}'...\n")
                log_widget.see(tk.END)
            logging.debug(f"Package '{package_name}' not found. Installing...")
            install_package(package, log_widget)
            if log_widget:
                log_widget.insert(tk.END, f"Package '{package}' installed.\n")
                log_widget.see(tk.END)
            logging.debug(f"Package '{package}' installed.")

    install_pywin32(log_widget)

    import requests
    import paramiko

    if restart_required:
        restart_script()

ssh_var_dict = {}
firewalls = []
server_types = []
locations = []
spec_slug_mapping = {}
spec_slug_label = None

import tkinter as tk

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None

        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)
        
        if isinstance(widget, ttk.Combobox):
            widget.bind("<<ComboboxSelected>>", self.hide_tooltip)
            widget.bind("<Button-1>", self.hide_tooltip)
            widget.bind("<ButtonRelease-1>", self.hide_tooltip)
            widget.bind("<FocusOut>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip_window is not None:
            return
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.withdraw()
        self.tooltip_window.overrideredirect(True)
        self.tooltip_window.attributes("-topmost", True)

        border_frame = tk.Frame(self.tooltip_window, bg="#0080FF", bd=1)
        border_frame.pack()
        label = tk.Label(border_frame,
                         text=self.text,
                         background="white",
                         fg="#333333",
                         relief="flat",
                         font=("Helvetica", 8),
                         padx=5,
                         pady=3)
        label.pack()
        self.tooltip_window.update_idletasks()

        tip_width = self.tooltip_window.winfo_width()
        tip_height = self.tooltip_window.winfo_height()

        root_window = self.widget.winfo_toplevel()
        root_window.update_idletasks()
        screen_width = root_window.winfo_screenwidth()
        screen_height = root_window.winfo_screenheight()

        main_x = root_window.winfo_rootx()
        main_y = root_window.winfo_rooty()
        main_w = root_window.winfo_width()
        main_h = root_window.winfo_height()

        offset = 20
        extra_for_top_bar = 20

        x_above = main_x + (main_w // 2) - (tip_width // 2)
        y_above = main_y - tip_height - offset - extra_for_top_bar

        if (x_above >= 0) and (y_above >= 0):
            final_x, final_y = x_above, y_above
        else:
            x_below = main_x + (main_w // 2) - (tip_width // 2)
            y_below = main_y + main_h + offset
            if ((x_below + tip_width) <= screen_width) and ((y_below + tip_height) <= screen_height):
                final_x, final_y = x_below, y_below
            else:
                final_x, final_y = 50, 50

        final_x = max(0, min(final_x, screen_width - tip_width))
        final_y = max(0, min(final_y, screen_height - tip_height))

        self.tooltip_window.geometry(f"+{final_x}+{final_y}")
        self.tooltip_window.deiconify()
        self.tooltip_window.lift()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

def format_path(path):
    if os.name == 'nt':
        return os.path.normpath(path)
    else:
        normalized_path = os.path.normpath(path)
        return normalized_path.replace('//', '/')

def get_cloud_config():
    """
    Determines which cloud provider to use based on the CLOUD_PROVIDER
    environment variable. Supported providers: "hetzner" or "digitalocean".
    Returns a configuration dictionary with API endpoints and default values.
    """
    provider = os.getenv("CLOUD_PROVIDER", "digitalocean").lower()

    if provider == "hetzner":
        config = {
            "provider": provider,
            "api_base_url": "https://api.hetzner.cloud/v1",
            "servers_endpoint": "https://api.hetzner.cloud/v1/servers",
            "ssh_keys_endpoint": "https://api.hetzner.cloud/v1/ssh_keys",
            "firewalls_endpoint": "https://api.hetzner.cloud/v1/firewalls",
            "default_server_type": "cx11",        # Example server type for Hetzner
            "default_image": "ubuntu-24.04",        # Default image for Ubuntu 24.04
            "default_region": None                # Hetzner doesn't require an explicit region here
        }
    elif provider == "digitalocean":
        config = {
            "provider": provider,
            "api_base_url": "https://api.digitalocean.com/v2",
            "servers_endpoint": "https://api.digitalocean.com/v2/droplets",
            "ssh_keys_endpoint": "https://api.digitalocean.com/v2/account/keys",
            "firewalls_endpoint": "https://api.digitalocean.com/v2/firewalls",
            "default_size": "s-1vcpu-1gb",          # DigitalOcean droplet size slug
            "default_image": "ubuntu-24-04-x64",      # Default image for Ubuntu 24.04
            "default_region": "nyc3"                # DigitalOcean region slug
        }
    else:
        raise ValueError(f"Unsupported cloud provider: {provider}")

    return config

def read_firewall_info_from_file(server_name):
    servers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SERVERS', server_name)
    ssh_config_file_path = os.path.join(servers_dir, f"{server_name}_ssh_config.txt")

    if not os.path.exists(ssh_config_file_path):
        print(f"SSH config file not found: {ssh_config_file_path}")
        return '', []

    firewall_name = ''
    firewall_rules = []

    with open(ssh_config_file_path, 'r') as f:
        lines = f.readlines()

    inside_firewall_rules = False
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("# Firewall Name:"):
            firewall_name = stripped_line[len("# Firewall Name:"):].strip()
        elif stripped_line == "# Firewall Rules:":
            inside_firewall_rules = True
            continue
        elif inside_firewall_rules:
            if stripped_line.startswith("# "):
                firewall_rules.append(stripped_line[2:])
            else:
                inside_firewall_rules = False

    return firewall_name, firewall_rules

def save_server_info(server_name, server_ip, ssh_key_path, username, network):
    servers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SERVERS', server_name)
    os.makedirs(servers_dir, exist_ok=True)
    ssh_config_file_path = os.path.join(servers_dir, f"{server_name}_ssh_config.txt")
    formatted_ssh_key_path = format_path(ssh_key_path)

    ssh_config_lines = [
        f"### This ssh_config file can also be used to import this server's settings into Termius. ###",
        "",
        f"Host {server_name}",
        f"    HostName {server_ip}",
        f"    User {username}",
        f"    IdentityFile {formatted_ssh_key_path}",
        "    Port 22",
        "",
    ]

    ssh_command = f"ssh -i {formatted_ssh_key_path} {username}@{server_ip}"
    sftp_command = f"sftp -i {formatted_ssh_key_path} {username}@{server_ip}"

    ssh_config_lines.extend([
        "",
        "# Commands to access the server:",
        f"# {ssh_command}",
        f"# {sftp_command}",
    ])

    with open(ssh_config_file_path, 'w') as f:
        f.write('\n'.join(ssh_config_lines))

    if platform.system() == "Darwin":
        # --- Create a duplicate (hard link if possible) in the user's .ssh folder ---
        user_ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
        os.makedirs(user_ssh_dir, exist_ok=True)
        destination_path = os.path.join(user_ssh_dir, f"{server_name}_ssh_config.txt")

        # Remove the destination file if it exists
        if os.path.exists(destination_path):
            os.remove(destination_path)

        try:
            # Attempt to create a hard link
            os.link(ssh_config_file_path, destination_path)
        except Exception as e:
            # If hard link fails (e.g., on some Windows setups), fallback to copying the file
            shutil.copy2(ssh_config_file_path, destination_path)

    # Chreate an importable termius.csv (But no ssh is imorted)
    # csv_file_path = os.path.join(servers_dir, f"{server_name}_termius.csv")
    # with open(csv_file_path, 'w', newline='') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(["Groups", "Label", "Tags", "Hostname/IP", "Protocol", "Port"])
    #     writer.writerow(["Nodes/DAG", server_name, network, server_ip, "ssh", "22"])
    
    # Return the path to the SSH config file
    return ssh_config_file_path

def get_firewall_details(api_key, firewall_id):
    """
    Fetches the details of a firewall from DigitalOcean.
    
    Parameters:
      - api_key: Your DigitalOcean API token.
      - firewall_id: The ID of the firewall to retrieve.
      
    Returns:
      A dictionary containing the firewall details (as returned by DigitalOcean).
      If the request fails, returns an empty dictionary.
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    url = f'https://api.digitalocean.com/v2/firewalls/{firewall_id}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('firewall', {})
    else:
        print(f"Failed to fetch firewall details: {response.text}")
        return {}
    
def save_config(config_data, config_file='config.txt'):
    with open(config_file, 'w') as file:
        for key, value in config_data.items():
            file.write(f'{key} = {value}\n')

def load_config(config_file='config.txt'):
    config = {}
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            for line in file:
                key_value = line.strip().split('=', 1)
                if len(key_value) == 2:
                    key, value = key_value
                    config[key.strip()] = value.strip()
    return config

def read_ssh_key_path(server_name):
    servers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SERVERS', server_name)
    ssh_config_file_path = os.path.join(servers_dir, f"{server_name}_ssh_config.txt")

    if not os.path.exists(ssh_config_file_path):
        print(f"SSH config file not found: {ssh_config_file_path}")
        return ''

    with open(ssh_config_file_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if 'IdentityFile' in line:
            ssh_key_path = line.strip().split(' ', 1)[1].strip()
            return ssh_key_path

    return ''

# Function to fetch firewalls, server types, and locations data
def fetch_data(api_key):
    """
    Fetches data from DigitalOcean:
      - Firewalls
      - Droplet sizes (server types)
      - Regions (locations)
      - Droplets (servers)
    
    Returns a tuple: (firewalls, server_types, locations, servers)
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Fetch firewalls
    firewall_url = 'https://api.digitalocean.com/v2/firewalls?per_page=200'
    try:
        firewall_response = requests.get(firewall_url, headers=headers)
        if firewall_response.status_code == 200:
            firewalls = firewall_response.json().get('firewalls', [])
        else:
            logging.error("Failed to fetch firewalls: %s", firewall_response.text)
            firewalls = []
    except Exception as e:
        logging.error("Exception while fetching firewalls: %s", e)
        firewalls = []
    logging.debug("Fetched %s firewalls", len(firewalls))
    
    # Fetch droplet sizes (server types)
    sizes_url = 'https://api.digitalocean.com/v2/sizes?per_page=200'
    try:
        sizes_response = requests.get(sizes_url, headers=headers)
        if sizes_response.status_code == 200:
            server_types = sizes_response.json().get('sizes', [])
        else:
            logging.error("Failed to fetch sizes: %s", sizes_response.text)
            server_types = []
    except Exception as e:
        logging.error("Exception while fetching sizes: %s", e)
        server_types = []
    logging.debug("Fetched %s sizes", len(server_types))
    
    # Fetch regions
    regions_url = 'https://api.digitalocean.com/v2/regions?per_page=200'
    try:
        regions_response = requests.get(regions_url, headers=headers)
        if regions_response.status_code == 200:
            locations = regions_response.json().get('regions', [])
        else:
            logging.error("Failed to fetch regions: %s", regions_response.text)
            locations = []
    except Exception as e:
        logging.error("Exception while fetching regions: %s", e)
        locations = []
    logging.debug("Fetched %s regions", len(locations))
    
    # Fetch droplets
    droplets_url = 'https://api.digitalocean.com/v2/droplets?per_page=200'
    try:
        droplets_response = requests.get(droplets_url, headers=headers)
        if droplets_response.status_code == 200:
            servers = droplets_response.json().get('droplets', [])
        else:
            logging.error("Failed to fetch droplets: %s", droplets_response.text)
            servers = []
    except Exception as e:
        logging.error("Exception while fetching droplets: %s", e)
        servers = []
    logging.debug("Fetched %s droplets", len(servers))
    
    return firewalls, server_types, locations, servers

def on_server_select(selected_server_var, status_text, api_key, *args):
    server_name = selected_server_var.get()
    if server_name:
        server_details = fetch_server_details(api_key, server_name)
        if server_details:
            status_text.delete('1.0', tk.END)
            status_text.insert(tk.END, f"Server: {server_name}\n")
            status_text.insert(tk.END, f"Host IP: {server_details['host_ip']}\n")
            status_text.insert(tk.END, f"SSH Key Path: {server_details['ssh_key_path']}\n")
            status_text.insert(tk.END, f"Firewall(s): {', '.join(server_details['firewalls'])}\n")
            status_text.insert(tk.END, f"Server Type: {server_details['server_type']}\n")
            status_text.insert(tk.END, f"Cores: {server_details['cores']}\n")
            status_text.insert(tk.END, f"Memory: {server_details['memory']} GB\n")
            status_text.insert(tk.END, f"Disk: {server_details['disk']} GB\n\n")
        else:
            status_text.insert(tk.END, "Error: Unable to fetch server details.\n")

def fetch_server_details(api_key, droplet_name):
    """
    Retrieves details for a droplet (server) on DigitalOcean.

    Parameters:
      - api_key: Your DigitalOcean API token.
      - droplet_name: The name of the droplet to retrieve details for.

    Returns:
      A dictionary with keys:
         - host_ip: The public IPv4 address of the droplet.
         - ssh_key_path: The locally stored SSH key path (using read_ssh_key_path).
         - firewalls: An empty list (DigitalOcean manages firewalls separately).
         - server_type: The droplet's size slug.
         - cores: Number of vCPUs.
         - memory: Memory (in MB) of the droplet.
         - disk: Disk size (in GB) of the droplet.
         - firewall_ids: An empty list (firewall assignments are managed separately).
      Returns None if droplet is not found or if an error occurs.
    """
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}

    # Fetch all droplets from DigitalOcean.
    droplets_url = 'https://api.digitalocean.com/v2/droplets'
    droplets_response = requests.get(droplets_url, headers=headers)
    if droplets_response.status_code != 200:
        print(f"Failed to fetch droplets: {droplets_response.status_code}")
        return None

    droplets = droplets_response.json().get('droplets', [])

    # Find the droplet by name (case-insensitive)
    droplet_summary = next((d for d in droplets if d['name'].lower() == droplet_name.lower()), None)
    if not droplet_summary:
        print(f"Droplet with name '{droplet_name}' not found.")
        return None

    droplet_id = droplet_summary['id']

    # Fetch droplet details using its ID.
    detail_url = f"https://api.digitalocean.com/v2/droplets/{droplet_id}"
    detail_response = requests.get(detail_url, headers=headers)
    if detail_response.status_code != 200:
        print(f"Failed to fetch droplet details: {detail_response.status_code}")
        return None

    droplet = detail_response.json().get('droplet', {})

    # Extract public IPv4 address from the networks list.
    public_ip = None
    for net in droplet.get("networks", {}).get("v4", []):
        if net.get("type") == "public":
            public_ip = net.get("ip_address")
            break

    # Retrieve local SSH key path using the provided helper.
    ssh_key_path = read_ssh_key_path(droplet_name)

    # DigitalOcean does not include firewall information in the droplet details.
    firewall_names = []
    firewall_ids = []

    return {
        'host_ip': public_ip,
        'ssh_key_path': ssh_key_path,
        'firewalls': firewall_names,
        'server_type': droplet.get("size_slug"),
        'cores': droplet.get("vcpus"),
        'memory': droplet.get("memory"),  # Memory in MB
        'disk': droplet.get("disk"),      # Disk in GB
        'firewall_ids': firewall_ids
    }

def create_new_firewall_with_defaults(api_key, firewall_name):
    """
    Creates a new firewall on DigitalOcean with default inbound and outbound rules.
    
    Inbound rules:
      - SSH (TCP port 22) with sources determined by the user (restricted to WAN IP if desired)
      - ICMP from anywhere (no "ports" field is sent)
      - TCP for ports 9000-9001 from anywhere
      - TCP for ports 9010-9011 from anywhere
      
    Outbound rules:
      - Allow all outbound TCP traffic (ports "all")
      - Allow all outbound UDP traffic (ports "all")
      - Allow all outbound ICMP traffic (no ports key)
    
    Parameters:
      - api_key: DigitalOcean API token.
      - firewall_name: The name for the new firewall.
    
    Returns:
      The ID of the created firewall if successful; otherwise, None.
    """
    from tkinter import messagebox, simpledialog
    import ipaddress
    import requests
    import json

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Get the user's WAN IP.
    wan_ip = get_wan_ip()
    if not wan_ip:
        messagebox.showerror("Error",
            "Failed to fetch your WAN IP address. Cannot restrict SSH access to your Home IP.")
        source_ips_ssh = ["0.0.0.0/0", "::/0"]
    else:
        message_text = f"Your current WAN IP address is: {wan_ip}\n\nDo you want to restrict SSH access to this IP for extra security?"
        add_home_ip = messagebox.askyesno("Add Extra Security", message_text)
        if add_home_ip:
            # Restrict SSH to WAN IP (using proper CIDR notation)
            source_ips_ssh = [f"{wan_ip}/32" if ':' not in wan_ip else f"{wan_ip}/128"]
            add_more_ips = messagebox.askyesno("Additional IPs", 
                "Would you like to add any other IP addresses or CIDR ranges to allow SSH access from?")
            if add_more_ips:
                while True:
                    additional_ips = simpledialog.askstring("Additional IPs",
                        "Enter additional IP addresses or CIDR ranges, separated by commas:\n"
                        "For IPs without a CIDR suffix, /32 is assumed for IPv4 and /128 for IPv6.")
                    if additional_ips:
                        additional_ips_list = [ip.strip() for ip in additional_ips.split(',') if ip.strip()]
                        processed_ips = []
                        invalid_ips = []
                        for ip in additional_ips_list:
                            original_ip = ip
                            if '/' not in ip:
                                try:
                                    ip_obj = ipaddress.ip_address(ip)
                                    ip = f"{ip}/32" if isinstance(ip_obj, ipaddress.IPv4Address) else f"{ip}/128"
                                except ValueError:
                                    invalid_ips.append(original_ip)
                                    continue
                            try:
                                ipaddress.ip_network(ip, strict=False)
                                processed_ips.append(ip)
                            except ValueError:
                                invalid_ips.append(original_ip)
                        if invalid_ips:
                            messagebox.showerror("Invalid IP(s)",
                                f"The following IP addresses or CIDR ranges are invalid:\n{', '.join(invalid_ips)}\nPlease enter valid values.")
                            continue
                        else:
                            source_ips_ssh.extend(processed_ips)
                            break
                    else:
                        break
        else:
            source_ips_ssh = ["0.0.0.0/0", "::/0"]

    # Build the inbound rules.
    inbound_rules = [
        {
            "protocol": "tcp",
            "ports": "22",
            "sources": {
                "addresses": source_ips_ssh
            }
        },
        {
            "protocol": "icmp",
            # For ICMP, omit the "ports" field.
            "sources": {
                "addresses": ["0.0.0.0/0", "::/0"]
            }
        },
        {
            "protocol": "tcp",
            "ports": "9000-9001",
            "sources": {
                "addresses": ["0.0.0.0/0", "::/0"]
            }
        },
        {
            "protocol": "tcp",
            "ports": "9010-9011",
            "sources": {
                "addresses": ["0.0.0.0/0", "::/0"]
            }
        }
    ]

    # Build the outbound rules as three separate rules.
    outbound_rules = [
        {
            "protocol": "tcp",
            "ports": "all",
            "destinations": {
                "addresses": ["0.0.0.0/0", "::/0"]
            }
        },
        {
            "protocol": "udp",
            "ports": "all",
            "destinations": {
                "addresses": ["0.0.0.0/0", "::/0"]
            }
        },
        {
            "protocol": "icmp",
            "destinations": {
                "addresses": ["0.0.0.0/0", "::/0"]
            }
        }
    ]

    payload = {
        "name": firewall_name,
        "inbound_rules": inbound_rules,
        "outbound_rules": outbound_rules
    }

    url = "https://api.digitalocean.com/v2/firewalls"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [201, 202]:
        fw = response.json().get('firewall', {})
        return fw.get('id')
    else:
        logging.error("Failed to create a new firewall: %s", response.text)
        messagebox.showerror("Error", f"Failed to create firewall. Status Code: {response.status_code}\nResponse: {response.text}")
        return None

def get_wan_ip():
    try:
        wan_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
        return wan_ip
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch WAN IP: {e}")
        return None

def secure_ssh_to_wan_ip():
    wan_ip = get_wan_ip()
    if not wan_ip:
        return

    for row in rules_frame.winfo_children():
        entries = [widget for widget in row.winfo_children() if isinstance(widget, (tk.Entry, ttk.Combobox, tk.Label))]
        if len(entries) >= 3:
            add_details, protocol_widget, port_range_widget = entries[:3]
            protocol = protocol_widget.cget("text") if isinstance(protocol_widget, tk.Label) else protocol_widget.get()
            port_range = port_range_widget.cget("text") if isinstance(port_range_widget, tk.Label) else port_range_widget.get()

            if port_range == "22" and protocol.lower() == "ssh":
                add_details_var_obj = ssh_var_dict.get(row)
                if add_details_var_obj:
                    new_value = wan_ip + "/32"
                    add_details_var_obj.set(new_value)

                for other_row in rules_frame.winfo_children():
                    if other_row != row:
                        other_entries = [widget for widget in other_row.winfo_children() if isinstance(widget, (tk.Entry, ttk.Combobox, tk.Label))]
                        if len(other_entries) >= 3:
                            other_protocol_widget, other_port_range_widget = other_entries[1:3]
                            other_protocol = other_protocol_widget.cget("text") if isinstance(other_protocol_widget, tk.Label) else other_protocol_widget.get()
                            other_port_range = other_port_range_widget.cget("text") if isinstance(other_port_range_widget, tk.Label) else other_port_range_widget.get()
                            if other_port_range == "22" and other_protocol.lower() == "ssh":
                                other_row.destroy()

def fetch_ssh_keys(api_key):
    """
    Fetches the list of SSH keys from DigitalOcean.

    Parameters:
      - api_key: (str) Your DigitalOcean API token.

    Returns:
      A list of SSH key objects as returned by DigitalOcean's API.
      If the request fails, returns an empty list.
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    url = 'https://api.digitalocean.com/v2/account/keys'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('ssh_keys', [])
    else:
        print('Failed to fetch SSH keys. Response:', response.text)
        return []

def update_firewall_dropdown(api_key, firewall_dropdown, selected_firewall_var):
    firewalls, _, _, _ = fetch_data(api_key)
    current_selection = selected_firewall_var.get()
    
    firewall_names = [fw['name'] for fw in firewalls]
    firewall_dropdown['values'] = firewall_names
    
    if current_selection not in firewall_names:
        selected_firewall_var.set('') 
        firewall_dropdown.set('') 

def create_edit_firewall_window(api_key, firewall_details, firewall_dropdown):
    edit_window = tk.Toplevel()    
    window_title = "Edit Firewall" if firewall_details.get('name') else "New Firewall"
    edit_window.title(window_title)
    edit_window.geometry("600x400")

    tk.Label(edit_window, text="Firewall Name:").pack()
    name_entry = tk.Entry(edit_window)
    name_entry.insert(0, firewall_details.get('name', firewall_dropdown.get()))
    name_entry.pack()

    global rules_frame
    rules_frame = tk.Frame(edit_window)
    rules_frame.pack()

    header_row = tk.Frame(rules_frame)
    header_row.pack(fill='x', padx=25, pady=2)
    tk.Label(header_row, text="Add Details", width=15, anchor='w').pack(side=tk.LEFT)
    tk.Label(header_row, text="Protocol", width=10, anchor='w').pack(side=tk.LEFT)
    tk.Label(header_row, text="Port Range", width=15, anchor='w').pack(side=tk.LEFT)

    # We use a helper dictionary (e.g. ssh_var_dict) to remember rows with fixed values.
    global ssh_var_dict
    ssh_var_dict = {}

    def add_rule_row(add_details="Any IPv4, Any IPv6", protocol="", port_range=""):
        row = tk.Frame(rules_frame)
        row.pack(fill='x', padx=5, pady=2)
        add_details_var = tk.StringVar(value=add_details)
        add_details_entry = tk.Entry(row, width=20, textvariable=add_details_var)
        add_details_entry.pack(side=tk.LEFT)
        # For SSH, force the protocol to be "tcp" and port "22"
        if protocol == "ssh" and port_range == "22":
            ssh_var_dict[row] = add_details_var
            tk.Label(row, text="tcp", width=10).pack(side=tk.LEFT)
            tk.Label(row, text="22", width=15).pack(side=tk.LEFT)
        elif protocol == "icmp":
            tk.Label(row, text="icmp", width=10).pack(side=tk.LEFT)
            tk.Label(row, text="", width=15).pack(side=tk.LEFT)
        else:
            protocol_options = ["tcp", "udp"]
            protocol_menu = ttk.Combobox(row, values=protocol_options, width=10)
            protocol_menu.set(protocol)
            protocol_menu.pack(side=tk.LEFT)
            port_range_var = tk.StringVar(value=port_range)
            port_range_entry = tk.Entry(row, width=15, textvariable=port_range_var)
            port_range_entry.pack(side=tk.LEFT)
            tk.Button(row, text="DELETE", command=lambda: row.destroy()).pack(side=tk.LEFT)

    if firewall_details.get('rules'):
        for rule in firewall_details['rules']:
            # For display, replace default DO shorthand with our UI terms.
            source_ips = ", ".join(rule.get('source_ips', [])).replace("0.0.0.0/0", "Any IPv4").replace("::/0", "Any IPv6")
            protocol = rule.get('protocol', '')
            port_range = rule.get('port', '') if rule.get('port') else ""
            if protocol == "tcp" and port_range == "22":
                add_rule_row(source_ips, "ssh", "22")
            elif protocol == "icmp":
                add_rule_row(source_ips, "icmp", "")
            else:
                add_rule_row(source_ips, protocol, port_range)
    else:
        # Default rules: SSH (tcp 22), ICMP (all), and two additional TCP rules.
        add_rule_row("Any IPv4, Any IPv6", "ssh", "22")
        add_rule_row("Any IPv4, Any IPv6", "icmp", "")
        add_rule_row("Any IPv4, Any IPv6", "tcp", "9000-9001")
        add_rule_row("Any IPv4, Any IPv6", "tcp", "9010-9011")

    tk.Button(edit_window, text="ADD", command=lambda: add_rule_row()).pack()
    tk.Button(edit_window, text="Secure Access to WAN IP", command=secure_ssh_to_wan_ip).pack(pady=5)
    tk.Button(edit_window, text="Save", width=20,
              command=lambda: save_firewall(api_key, name_entry.get(), rules_frame,
                                             firewall_details.get('id'), firewall_dropdown, edit_window)
             ).pack(side=tk.BOTTOM, pady=10)


def save_firewall(api_key, new_name, rules_frame, firewall_id, firewall_dropdown, edit_window):
    """
    Updates or creates a DigitalOcean firewall using rules gathered from the UI.
    Validates that:
      - Each rule has a protocol in {"tcp", "udp", "icmp"}.
      - For tcp/udp rules, a valid port or port range is provided.
      - For icmp rules, no 'ports' key is sent.
    Forces an SSH rule (tcp port 22) as the first rule.
    Outbound rules are explicitly defined for TCP and UDP with the full port range.
    """
    import re, json
    allowed_protocols = {"tcp", "udp", "icmp"}
    # A valid port range is a single number or a range like "9000-9010".
    port_range_pattern = re.compile(r'^\d+(-\d+)?$')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    updated_inbound_rules = []
    for row in rules_frame.winfo_children():
        # Get all Entry, Combobox, or Label widgets.
        entries = [w for w in row.winfo_children() if isinstance(w, (tk.Entry, ttk.Combobox, tk.Label))]
        # Skip header rows.
        if any(isinstance(w, tk.Label) and w.cget("text") in ["Add Details", "Protocol", "Port Range"] for w in entries):
            continue
        if len(entries) < 2:
            continue
        protocol = (entries[1].cget("text") if isinstance(entries[1], tk.Label) else entries[1].get()).strip().lower()
        if protocol not in allowed_protocols:
            logging.debug("Skipping rule with unrecognized protocol: '%s'", protocol)
            continue
        add_details = entries[0].get().strip()
        source_addresses = [
            ip.strip().replace("Any IPv4", "0.0.0.0/0").replace("Any IPv6", "::/0")
            for ip in add_details.split(",") if ip.strip()
        ]
        rule = {"protocol": protocol, "sources": {"addresses": source_addresses}}
        if protocol in {"tcp", "udp"}:
            if len(entries) < 3:
                logging.debug("Skipping rule for protocol %s due to missing port information.", protocol)
                continue
            port_val = (entries[2].cget("text") if isinstance(entries[2], tk.Label) else entries[2].get()).strip()
            if not port_range_pattern.match(port_val):
                logging.debug("Skipping rule with invalid port range '%s' for protocol %s", port_val, protocol)
                continue
            rule["ports"] = port_val
        updated_inbound_rules.append(rule)
    
    # Force the SSH rule (tcp port 22) as the first rule.
    ssh_rule = {"protocol": "tcp", "ports": "22", "sources": {"addresses": ["0.0.0.0/0", "::/0"]}}
    # Remove any existing SSH rule to avoid duplicates.
    updated_inbound_rules = [r for r in updated_inbound_rules if not (r["protocol"] == "tcp" and r.get("ports") == "22")]
    updated_inbound_rules.insert(0, ssh_rule)
    # Ensure an ICMP rule is present (without a ports key).
    if not any(r["protocol"] == "icmp" for r in updated_inbound_rules):
        icmp_rule = {"protocol": "icmp", "sources": {"addresses": ["0.0.0.0/0", "::/0"]}}
        updated_inbound_rules.append(icmp_rule)
    
    # Outbound rules: two rules for TCP and UDP covering all ports.
    outbound_rules = [
        {"protocol": "tcp", "ports": "1-65535", "destinations": {"addresses": ["0.0.0.0/0", "::/0"]}},
        {"protocol": "udp", "ports": "1-65535", "destinations": {"addresses": ["0.0.0.0/0", "::/0"]}}
    ]
    
    # Always include the firewall name in the payload.
    payload = {
        "name": new_name,
        "inbound_rules": updated_inbound_rules,
        "outbound_rules": outbound_rules
    }
    
    if not firewall_id:
        url = "https://api.digitalocean.com/v2/firewalls"
        response = requests.post(url, headers=headers, json=payload)
    else:
        url = f"https://api.digitalocean.com/v2/firewalls/{firewall_id}"
        response = requests.put(url, headers=headers, json=payload)
    
    logging.debug("Payload Sent:\n%s", payload)
    try:
        resp_json = response.json()
    except Exception:
        resp_json = response.text
    logging.debug("API Response:\n%s", resp_json)
    
    if response.status_code in [200, 201, 202]:
        messagebox.showinfo("Success", "Firewall updated successfully.\n\n" + json.dumps(resp_json, indent=2))
        # Refresh the firewall dropdown.
        firewalls, _, _, _ = fetch_data(api_key)
        firewall_dropdown['values'] = [fw['name'] for fw in firewalls]
        edit_window.destroy()
    else:
        messagebox.showerror("Error", f"Failed to update firewall. Status Code: {response.status_code}\nResponse: {response.text}\nURL: {url}")

def delete_firewall(api_key, firewall_name, firewall_dropdown, selected_firewall):
    """
    Deletes a firewall from DigitalOcean.

    Parameters:
      - api_key: Your DigitalOcean API token.
      - firewall_name: Name of the firewall to delete.
      - firewall_dropdown: UI dropdown widget for firewalls.
      - selected_firewall: Tkinter variable holding the currently selected firewall.
    """
    confirm = messagebox.askyesno(
        "Confirm Delete",
        f"Are you sure you want to delete the firewall '{firewall_name}'? This action cannot be undone."
    )
    if not confirm:
        return

    # Fetch current firewalls using DigitalOcean's API.
    firewalls, _, _, _ = fetch_data(api_key)
    # Find the firewall by name.
    firewall = next((fw for fw in firewalls if fw['name'] == firewall_name), None)
    if not firewall:
        messagebox.showerror("Error", "Firewall not found.")
        return

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    url = f'https://api.digitalocean.com/v2/firewalls/{firewall["id"]}'
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        messagebox.showinfo("Success", "Firewall deleted successfully.")
        update_firewall_dropdown(api_key, firewall_dropdown, selected_firewall, lambda: None)
    else:
        messagebox.showerror("Error", f"Failed to delete firewall. Status Code: {response.status_code}")

def edit_firewall(api_key, firewall_name, firewall_dropdown):
    firewalls, _, _, _ = fetch_data(api_key)
    firewall = next((fw for fw in firewalls if fw['name'] == firewall_name), None)
    if not firewall:
        messagebox.showerror("Error", "Firewall not found.")
        return
    create_edit_firewall_window(api_key, firewall, firewall_dropdown)

def import_ssh(api_key, ssh_name, ssh_dropdown):
    """
    Imports a local SSH key to DigitalOcean.
    
    It reads the public key from ~/.ssh/{ssh_name}.pub and sends it
    to DigitalOcean's /v2/account/keys endpoint.
    
    Parameters:
      - api_key: DigitalOcean API token.
      - ssh_name: Name of the SSH key.
      - ssh_dropdown: Reference to the UI dropdown to update after import.
    """
    key_path = os.path.expanduser(f"~/.ssh/{ssh_name}")
    if not os.path.exists(key_path) or not os.path.exists(f"{key_path}.pub"):
        messagebox.showerror("Error", "Local SSH Key files not found.")
        return

    with open(f"{key_path}.pub", "r") as file:
        public_key = file.read().strip()

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    url = "https://api.digitalocean.com/v2/account/keys"
    data = {'name': ssh_name, 'public_key': public_key}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        messagebox.showinfo("Success", f"SSH Key '{ssh_name}' imported successfully to DigitalOcean.")

        ssh_keys = fetch_ssh_keys(api_key)

        ssh_dir = os.path.expanduser("~/.ssh")
        if os.path.exists(ssh_dir):
            local_ssh_keys = [f for f in os.listdir(ssh_dir) if f.endswith('.pub')]
            local_ssh_keys = [os.path.splitext(f)[0] for f in local_ssh_keys]
        else:
            local_ssh_keys = []

        ssh_names = [ssh['name'] for ssh in ssh_keys]
        for local_key in local_ssh_keys:
            if local_key not in ssh_names:
                ssh_keys.append({'name': f"Local: {local_key}", 'local_only': True})

        ssh_dropdown['values'] = [ssh['name'] for ssh in ssh_keys]
    else:
        messagebox.showerror("Error", f"Failed to import SSH key to DigitalOcean. Response: {response.text}")

def create_ssh_key(api_key, ssh_key_name, passphrase, ssh_dropdown):
    """
    Creates a new SSH key on DigitalOcean.
    
    Parameters:
      - api_key: Your DigitalOcean API token.
      - ssh_key_name: Name for the SSH key.
      - passphrase: Passphrase for generating the key.
      - ssh_dropdown: UI element for updating the list (if needed).
    
    Returns:
      The ID of the newly created SSH key on DigitalOcean.
      Returns None if creation fails.
    """
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    url = "https://api.digitalocean.com/v2/account/keys"
    
    # Check if the key already exists on DigitalOcean.
    ssh_keys = fetch_ssh_keys(api_key)
    if any(ssh['name'] == ssh_key_name for ssh in ssh_keys):
        messagebox.showwarning("SSH Key Exists", f"The SSH key '{ssh_key_name}' already exists on DigitalOcean.")
        return None

    key_path = os.path.expanduser(f"~/.ssh/{ssh_key_name}")
    if os.path.exists(key_path) or os.path.exists(f"{key_path}.pub"):
        messagebox.showerror("Error", "The SSH key already exists locally and cannot be overwritten.")
        return None

    if passphrase is None:
        passphrase = simpledialog.askstring("Passphrase", f"Enter passphrase for SSH key '{ssh_key_name}':", show='*')
    if passphrase is None:
        messagebox.showinfo("Cancelled", "SSH key creation cancelled.")
        return None

    if platform.system() == "Windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        cmd = f'ssh-keygen -t rsa -b 4096 -f "{key_path}" -N "{passphrase}" -C "{ssh_key_name}"'
        result = subprocess.run(
            cmd,
            shell=True,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW,
            capture_output=True,
            text=True
        )
    else:
        escaped_passphrase = passphrase.replace('"', '\\"')
        cmd = ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", key_path, "-N", escaped_passphrase, "-C", ssh_key_name]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

    if result.returncode != 0:
        logging.error(f"Failed to generate SSH key locally. Error: {result.stderr}")
        return None

    try:
        with open(f"{key_path}.pub", "r") as file:
            public_key = file.read().strip()
    except Exception as e:
        logging.error(f"Failed to read the public key file: {e}")
        messagebox.showerror("Error", f"Failed to read the public key file: {e}")
        return None

    data = {'name': ssh_key_name, 'public_key': public_key}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        if response.status_code == 201:
            # DigitalOcean returns the new key under "ssh_key"
            ssh_key_id = response_data.get('ssh_key', {}).get('id')
            logging.info(f"SSH Key '{ssh_key_name}' created successfully with ID: {ssh_key_id}")
            return ssh_key_id
        else:
            logging.error(f"Failed to create SSH key on DigitalOcean. Status Code: {response.status_code}. Response: {response_data}")
            messagebox.showerror("Error", f"Failed to create SSH key on DigitalOcean. Response: {response_data}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Exception occurred while creating SSH key on DigitalOcean: {e}")
        messagebox.showerror("Error", f"Failed to create SSH key on DigitalOcean due to a network error: {e}")
        return None

def delete_ssh_key(api_key, ssh_key_name, ssh_dropdown, selected_ssh, update_ssh_buttons):
    """
    Deletes an SSH key from DigitalOcean.

    Parameters:
      - api_key: Your DigitalOcean API token.
      - ssh_key_name: Name of the SSH key to delete.
      - ssh_dropdown: UI dropdown for SSH keys (to refresh after deletion).
      - selected_ssh: Variable holding the currently selected SSH key.
      - update_ssh_buttons: Callback function to update the SSH buttons in the UI.
    """
    confirm = messagebox.askyesno(
        "Confirm Delete",
        f"Are you sure you want to delete the SSH key '{ssh_key_name}'? This action cannot be undone."
    )
    if not confirm:
        return

    # If the key is a local-only key, delete it locally.
    if ssh_key_name.startswith("Local: "):
        local_key_name = ssh_key_name.replace("Local: ", "")
        key_path = os.path.expanduser(f"~/.ssh/{local_key_name}")
        if os.path.exists(key_path):
            os.remove(key_path)
        if os.path.exists(f"{key_path}.pub"):
            os.remove(f"{key_path}.pub")
        messagebox.showinfo("Success", "Local SSH Key deleted successfully.")
        update_ssh_dropdown(api_key, ssh_dropdown, selected_ssh, update_ssh_buttons)
    else:
        # Fetch the key from DigitalOcean
        ssh_keys = fetch_ssh_keys(api_key)
        ssh_key = next((key for key in ssh_keys if key['name'] == ssh_key_name), None)
        if not ssh_key:
            messagebox.showerror("Error", "SSH Key not found on DigitalOcean.")
            return

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        url = f'https://api.digitalocean.com/v2/account/keys/{ssh_key["id"]}'
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            messagebox.showinfo("Success", "DigitalOcean SSH Key deleted successfully.")
            update_ssh_dropdown(api_key, ssh_dropdown, selected_ssh, update_ssh_buttons)
        else:
            messagebox.showerror("Error", f"Failed to delete SSH key from DigitalOcean. Status Code: {response.status_code}")

def update_ssh_dropdown(api_key, ssh_dropdown, selected_ssh, update_ssh_buttons):
    """
    Refreshes the SSH key dropdown using DigitalOcean's API.
    
    It calls fetch_ssh_keys() (which is now the DigitalOcean version) and then adds any local SSH keys 
    that haven't been imported to DigitalOcean.
    
    Parameters:
      - api_key: DigitalOcean API token.
      - ssh_dropdown: The UI dropdown widget to update.
      - selected_ssh: A Tkinter variable holding the currently selected SSH key.
      - update_ssh_buttons: Callback to update UI buttons related to SSH keys.
    """
    ssh_keys = fetch_ssh_keys(api_key)
    
    # Get the list of local SSH key names from ~/.ssh
    local_ssh_keys = [f for f in os.listdir(os.path.expanduser("~/.ssh")) if f.endswith('.pub')]
    local_ssh_keys = [os.path.splitext(f)[0] for f in local_ssh_keys]
    
    # Build a list of names from the keys fetched from DigitalOcean
    ssh_names = [ssh['name'] for ssh in ssh_keys]
    for local_key in local_ssh_keys:
        if local_key not in ssh_names:
            ssh_keys.append({'name': f"Local: {local_key}", 'local_only': True})
    
    ssh_dropdown['values'] = [ssh['name'] for ssh in ssh_keys]
    selected_ssh.set('')
    update_ssh_buttons()

def remove_ip_from_known_hosts(server_ip):
    known_hosts_path = format_path(os.path.expanduser("~/.ssh/known_hosts"))
    if not os.path.exists(known_hosts_path):
        return

    with open(known_hosts_path, 'r') as file:
        lines = file.readlines()

    with open(known_hosts_path, 'w') as file:
        for line in lines:
            if server_ip not in line:
                file.write(line)
            else:
                print(f"Removed offending IP {server_ip} from known_hosts.")

import os
# import requests
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import shutil

def create_server(
    api_key, 
    droplet_name,          # Name for the droplet
    size_slug,             # DigitalOcean size slug (e.g. "s-1vcpu-1gb")
    distribution,          # Chosen distribution (e.g. "ubuntu-22.04")
    region_slug,           # Region slug (e.g. "nyc3", "fra1")
    selected_ssh_key_name, 
    ssh_dropdown,
    create_button          # The "Create Server" button widget that will show the countdown
):
    import requests, os, shutil, subprocess, time
    from tkinter import messagebox, filedialog, simpledialog

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    _, _, _, droplets = fetch_data(api_key)
    for droplet in droplets:
        if droplet.get('name', '').lower() == droplet_name.lower():
            messagebox.showerror("Error", f"Droplet with name '{droplet_name}' already exists.")
            return
            
    # Retrieve SSH keys from DigitalOcean.
    ssh_keys = fetch_ssh_keys(api_key)
    ssh_key = next((key for key in ssh_keys if key['name'] == selected_ssh_key_name), None)

    local_private_key_path = os.path.expanduser(f"~/.ssh/{selected_ssh_key_name}")
    local_public_key_path = f"{local_private_key_path}.pub"

    ssh_private_key_exists = os.path.isfile(local_private_key_path)
    ssh_public_key_exists = os.path.isfile(local_public_key_path)

    # Reconcile local vs. remote SSH keys.
    if ssh_private_key_exists and not ssh_key:
        if messagebox.askyesno("Import SSH Key",
            f"The SSH key '{selected_ssh_key_name}' exists locally but not on DigitalOcean.\n\nDo you want to import it now?"):
            import_ssh(api_key, selected_ssh_key_name, ssh_dropdown)
            ssh_key = next((key for key in fetch_ssh_keys(api_key) if key['name'] == selected_ssh_key_name), None)
            if not ssh_key:
                messagebox.showerror("Error", "Failed to import SSH key to DigitalOcean.")
                return
        else:
            messagebox.showinfo("Operation Cancelled", "Droplet creation cancelled.")
            return
    elif ssh_key and not ssh_private_key_exists:
        if messagebox.askyesno("Locate SSH Key",
            f"The SSH key '{selected_ssh_key_name}' exists on DigitalOcean but not locally.\n\nDo you want to locate the SSH private key?"):
            ssh_file_path = filedialog.askopenfilename(title='Select SSH Private Key', initialdir=os.path.expanduser('~'))
            if ssh_file_path:
                if os.path.isfile(ssh_file_path + '.pub'):
                    with open(ssh_file_path + '.pub', 'r') as pub_key_file:
                        local_public_key = pub_key_file.read().strip()
                    if 'public_key' in ssh_key and local_public_key == ssh_key['public_key'].strip():
                        messagebox.showinfo("Success", "SSH key validated successfully.")
                        destination_private_key = os.path.expanduser(f'~/.ssh/{selected_ssh_key_name}')
                        destination_public_key = os.path.expanduser(f'~/.ssh/{selected_ssh_key_name}.pub')
                        if os.path.exists(destination_private_key) or os.path.exists(destination_public_key):
                            messagebox.showwarning("File Exists",
                                "The SSH key files already exist in '~/.ssh/'. They will not be overwritten.")
                        else:
                            try:
                                shutil.copy2(ssh_file_path, destination_private_key)
                                shutil.copy2(ssh_file_path + '.pub', destination_public_key)
                                messagebox.showinfo("Success", "SSH key files copied to '~/.ssh/'.")
                            except Exception as e:
                                messagebox.showerror("Error", f"Failed to copy SSH key files: {e}")
                                return
                        local_private_key_path = destination_private_key
                        local_public_key_path = destination_public_key
                    else:
                        messagebox.showerror("Validation Failed", "The selected SSH key does not match the one on DigitalOcean.")
                        return
                else:
                    messagebox.showerror("Error", "Public key file not found alongside the private key.")
                    return
            else:
                messagebox.showinfo("Operation Cancelled", "Droplet creation cancelled.")
                return
        else:
            messagebox.showinfo("Operation Cancelled", "Droplet creation cancelled.")
            return
    elif not ssh_key and not ssh_private_key_exists:
        passphrase = simpledialog.askstring(
            "Passphrase", 
            f"Enter passphrase for the new SSH key '{selected_ssh_key_name}':",
            show='*'
        )
        if passphrase is not None:
            create_ssh_key(api_key, selected_ssh_key_name, passphrase, ssh_dropdown)
            ssh_key = next((key for key in fetch_ssh_keys(api_key) if key['name'] == selected_ssh_key_name), None)
            if not ssh_key:
                messagebox.showerror("Error", "Failed to create SSH key on DigitalOcean.")
                return
        else:
            messagebox.showinfo("Operation Cancelled", "Droplet creation cancelled.")
            return

    if not ssh_key:
        messagebox.showerror("Error", "SSH key is not available. Cannot proceed.")
        return

    # Use the DO SSH key id.
    ssh_key_id = ssh_key.get('id')
    print(f"Using SSH key with ID {ssh_key_id} and name '{selected_ssh_key_name}'.")

    # Map distribution to a valid DO image slug.
    valid_images = {
        "ubuntu-22.04": "ubuntu-22-04-x64",
        "ubuntu-24.04": "ubuntu-24-04-x64",
        "debian-12": "debian-12-x64"
    }
    image_slug = valid_images.get(distribution, distribution)

    # Build the droplet creation payload.
    payload = {
        "name": droplet_name,
        "region": region_slug,
        "size": size_slug,
        "image": image_slug,
        "ssh_keys": [ssh_key_id],
        "ipv6": True
    }

    url = "https://api.digitalocean.com/v2/droplets"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 202:
        droplet = response.json().get("droplet")
        if droplet:
            droplet_id = droplet.get("id")
            # Disable the Create Server button and show a countdown.
            create_button.config(state=tk.DISABLED)
            timeout = 180  # 3 minutes
            start_time = time.time()
            public_ip = None
            while not public_ip and (time.time() - start_time < timeout):
                elapsed = int(time.time() - start_time)
                create_button.config(text=f"Waiting... {elapsed} sec")
                create_button.update_idletasks()
                time.sleep(5)
                detail_url = f"https://api.digitalocean.com/v2/droplets/{droplet_id}"
                detail_response = requests.get(detail_url, headers=headers)
                if detail_response.status_code == 200:
                    droplet_details = detail_response.json().get("droplet", {})
                    networks = droplet_details.get("networks", {}).get("v4", [])
                    for net in networks:
                        if net.get("type") == "public":
                            public_ip = net.get("ip_address")
                            break
            # Re-enable the button and reset its text.
            create_button.config(state=tk.NORMAL, text="Create Server")
            if not public_ip:
                messagebox.showerror("Error", "Failed to retrieve public IP for droplet within timeout.")
                return

            remove_ip_from_known_hosts(public_ip)
            ssh_key_path = local_private_key_path
            username = 'root'
            server_info_file = save_server_info(droplet_name, public_ip, ssh_key_path, username, "")
            message_text = (
                f"Droplet '{droplet_name}' created successfully.\n\n"
                f"ID: {droplet_id}\n"
                f"IPv4: {public_ip}\n\n"
                f"Server information saved to:\n{server_info_file}"
            )
            if os.name == 'nt':
                if messagebox.askyesno("Success", f"{message_text}\n\nDo you want to open the server info file?"):
                    os.startfile(server_info_file)
            else:
                if messagebox.askyesno("Success", f"{message_text}\n\nDo you want to open the server info file?"):
                    if platform.system() == "Darwin":
                        subprocess.call(['open', server_info_file])
                    elif platform.system() == "Linux":
                        subprocess.call(['xdg-open', server_info_file])
        else:
            messagebox.showerror("Error", "Droplet creation succeeded but no droplet data returned.")
    else:
        messagebox.showerror("Error", f"Failed to create droplet. Response: {response.text}")

def get_available_nodectl_versions():
    from packaging import version as packaging_version
    url = "https://api.github.com/repos/StardustCollective/nodectl/releases"
    try:
        response = requests.get(url)
        response.raise_for_status()
        releases = response.json()
        
        versions = []
        for release in releases:
            tag_name = release.get("tag_name")
            is_prerelease = release.get("prerelease", False)
            parsed_version = packaging_version.parse(tag_name.lstrip('v'))
            versions.append({
                "tag_name": tag_name,
                "parsed_version": parsed_version,
                "is_prerelease": is_prerelease
            })
        
        versions.sort(key=lambda x: x["parsed_version"], reverse=True)
        
        # Get the latest stable version (non-prerelease)
        latest_stable_version = next((v for v in versions if not v["is_prerelease"]), None)
        if latest_stable_version:
            latest_version_tag = latest_stable_version["tag_name"]
        else:
            latest_version_tag = versions[0]["tag_name"] if versions else "unknown version"
        
        # Return a list of version tags including pre-releases
        version_tags = [v["tag_name"] for v in versions]
        return version_tags, latest_version_tag
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch nodectl versions: {e}")
        return [], "unknown version"

def get_latest_nodectl_version():
    url = "https://api.github.com/repos/StardustCollective/nodectl/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()
        latest_release = response.json()
        return latest_release.get("tag_name", "unknown version")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch the latest nodectl version: {e}")
        return "unknown version"

class PasswordDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()

        self.geometry(f"+{parent.winfo_rootx() + int(parent.winfo_width() / 2) - 100}+{parent.winfo_rooty() + int(parent.winfo_height() / 2) - 50}")

        self.value = None

        tk.Label(self, text=prompt).pack(padx=10, pady=10)

        self.password_var = tk.StringVar()
        self.show_password = tk.BooleanVar(value=False)

        self.entry = tk.Entry(self, textvariable=self.password_var, show="*")
        self.entry.pack(padx=10, pady=(0, 10))

        self.deiconify()
        self.lift()
        self.entry.focus_set()
        self.entry.icursor(tk.END)

        self.show_button = tk.Checkbutton(self, text="Show", variable=self.show_password, command=self.toggle_password)
        self.show_button.pack(pady=(0, 10))

        self.ok_button = tk.Button(self, text="OK", command=self.on_ok)
        self.ok_button.pack(pady=(0, 10))

        self.bind("<Return>", self.on_enter)
        self.bind("<Escape>", self.on_cancel)

    def toggle_password(self):
        if self.show_password.get():
            self.entry.config(show="")
        else:
            self.entry.config(show="*")

    def on_ok(self):
        self.value = self.password_var.get()
        self.destroy()

    def on_enter(self, event):
        self.on_ok()

    def on_cancel(self, event=None):
        self.destroy()

    @classmethod
    def ask_password(cls, parent, title, prompt):
        dialog = cls(parent, title, prompt)
        parent.wait_window(dialog)
        return dialog.value

def create_unix_aliases(server_name, ssh_command, sftp_command):
    home_dir = os.path.expanduser('~')
    bin_dir = os.path.join(home_dir, 'bin')
    os.makedirs(bin_dir, exist_ok=True)

    bashrc_path = os.path.join(home_dir, '.bashrc')
    with open(bashrc_path, 'a') as bashrc:
        bashrc.write('\n# Add ~/bin to PATH\n')
        bashrc.write('export PATH="$HOME/bin:$PATH"\n')

    ssh_script_path = os.path.join(bin_dir, f"{server_name}_ssh")
    with open(ssh_script_path, 'w') as ssh_script:
        ssh_script.write(f"#!/bin/bash\n{ssh_command} \"$@\"\n")
    os.chmod(ssh_script_path, 0o755)

    sftp_script_path = os.path.join(bin_dir, f"{server_name}_sftp")
    with open(sftp_script_path, 'w') as sftp_script:
        sftp_script.write(f"#!/bin/bash\n{sftp_command} \"$@\"\n")
    os.chmod(sftp_script_path, 0o755)

def create_windows_shortcuts(server_name, ssh_command, sftp_command):
    import pythoncom
    import win32com.client

    shell = win32com.client.Dispatch("WScript.Shell")
    desktop_path = shell.SpecialFolders("Desktop")

    ssh_shortcut_path = os.path.join(desktop_path, f"{server_name} SSH.lnk")
    create_windows_shortcut_from_command(ssh_shortcut_path, ssh_command, "SSH Shortcut")

    sftp_shortcut_path = os.path.join(desktop_path, f"{server_name} SFTP.lnk")
    create_windows_shortcut_from_command(sftp_shortcut_path, sftp_command, "SFTP Shortcut")

def create_windows_shortcut_from_command(shortcut_path, command, description):
    try:
        import pythoncom
        import win32com.client
        from shutil import which
        import shlex
    except ImportError:
        print("PyWin32 is not installed. Cannot create shortcuts.")
        return
    
    pythoncom.CoInitialize()

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)

    cmd_parts = shlex.split(command)
    executable = cmd_parts[0]
    arguments = ' '.join(cmd_parts[1:])

    target = None
    executable_name = executable.lower()

    if executable_name == 'ssh':
        possible_executables = [
            'ssh.exe',
        ]
    elif executable_name == 'sftp':
        possible_executables = [
            'sftp.exe',
        ]
    else:
        possible_executables = [executable]

    for exec_name in possible_executables:
        target = which(exec_name)
        if target and os.path.isfile(target):
            break
        else:
            target = None

    if not target:
        if executable_name == 'ssh':
            possible_paths = [
                r'C:\Windows\System32\OpenSSH\ssh.exe',
                r'C:\Program Files\Git\usr\bin\ssh.exe',
                r'C:\Program Files\OpenSSH-Win64\ssh.exe',
            ]
        elif executable_name == 'sftp':
            possible_paths = [
                r'C:\Windows\System32\OpenSSH\sftp.exe',
                r'C:\Program Files\Git\usr\bin\sftp.exe',
                r'C:\Program Files\OpenSSH-Win64\sftp.exe',
            ]
        else:
            possible_paths = []

        for path in possible_paths:
            if os.path.exists(path):
                target = path
                break

    if not target:
        print(f"Executable {executable} not found in PATH or default locations.")
        return
    
    shortcut.Targetpath = target
    shortcut.Arguments = arguments
    shortcut.WorkingDirectory = os.getcwd()
    shortcut.Description = description

    if "ssh" in executable.lower():
        shortcut.IconLocation = r'%SystemRoot%\system32\SHELL32.dll,135'
    elif "sftp" in executable.lower():
        shortcut.IconLocation = r'%SystemRoot%\system32\SHELL32.dll,146'
    else:
        shortcut.IconLocation = r'%SystemRoot%\system32\SHELL32.dll,1'

    shortcut.save()

def start_install_nodectl(api_key, server_name, ssh_key, status_text, p12_file, node_username, network, nodectl_version, parent_window, create_shortcuts_var, export_to_putty):
    ssh_passphrase = PasswordDialog.ask_password(parent_window, "SSH Passphrase", f"Enter passphrase for SSH key '{ssh_key}':")
    if not ssh_passphrase:
        status_text.insert(tk.END, "Installation canceled by the user.\n")
        return

    node_userpass = PasswordDialog.ask_password(parent_window, "Node Username Password", "Enter password for the node username:")
    if not node_userpass:
        status_text.insert(tk.END, "Installation canceled by the user.\n")
        return

    p12_passphrase = None

    # If a P12 file is provided, verify the P12 passphrase
    if p12_file:
        from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
        from cryptography.hazmat.backends import default_backend

        while True:
            p12_passphrase = PasswordDialog.ask_password(parent_window, "P12 Passphrase", "Enter passphrase for the P12 file:")
            if not p12_passphrase:
                status_text.insert(tk.END, "Installation canceled by the user.\n")
                return

            # Verify if the P12 passphrase is correct before proceeding
            try:
                with open(p12_file, 'rb') as f:
                    private_key, certificate, additional_certs = load_key_and_certificates(
                        f.read(),
                        p12_passphrase.encode() if p12_passphrase else None,
                        default_backend()
                    )

                if not private_key or not certificate:
                    raise ValueError("P12 passphrase incorrect or failed to extract key and certificate.")
                else:
                    status_text.insert(tk.END, "P12 passphrase verified successfully.\n")
                    break
            except (ValueError, Exception) as e:
                status_text.insert(tk.END, "Incorrect P12 passphrase. Please try again.\n")

    # If no P12 file is provided, prompt the user to create a new passphrase
    else:
        p12_passphrase = PasswordDialog.ask_password(parent_window, "Create P12 Passphrase", "Enter a passphrase to secure the new P12 file:")
        if not p12_passphrase:
            status_text.insert(tk.END, "Installation canceled by the user.\n")
            return
        status_text.insert(tk.END, "P12 passphrase created successfully.\n")

    log_window = tk.Toplevel(parent_window)
    log_window.title("Dependency Installation Progress")
    log_window.geometry("600x400")

    log_text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD, height=20, width=70)
    log_text.pack(pady=10, padx=10)

    install_required_packages(log_text)
    
    log_window.destroy()
    log_queue = queue.Queue()

    create_shortcuts = create_shortcuts_var.get()

    install_thread = threading.Thread(
        target=install_nodectl_thread, 
        args=(
            api_key, server_name, ssh_key, log_queue, ssh_passphrase, node_userpass, 
            p12_passphrase, p12_file, node_username, network, nodectl_version, 
            parent_window, create_shortcuts, export_to_putty
        )
    )
    install_thread.start()

    process_log_thread = threading.Thread(target=process_log_queue, args=(status_text, log_queue))
    process_log_thread.start()

def download_nodectl(client, nodectl_version, log_queue, distribution="ubuntu-22.04"):
    if distribution == "ubuntu-24.04":
        install_command = (
            f'sudo nodectl auto_restart disable; '
            f'wget -N https://github.com/stardustcollective/nodectl/releases/download/{nodectl_version}/nodectl_x86_64_2404 '
            f'-P /usr/local/bin -O /usr/local/bin/nodectl && sudo chmod +x /usr/local/bin/nodectl'
        )
    else:
        install_command = (
            f'sudo nodectl auto_restart disable; '
            f'wget -N https://github.com/stardustcollective/nodectl/releases/download/{nodectl_version}/nodectl_x86_64 '
            f'-P /usr/local/bin -O /usr/local/bin/nodectl && sudo chmod +x /usr/local/bin/nodectl'
        )

    max_retries = 3
    for attempt in range(max_retries):
        stdin, stdout, stderr = client.exec_command(install_command)
        stdout_output = stdout.read().decode('utf-8')
        stderr_output = stderr.read().decode('utf-8')

        if "502 Bad Gateway" not in stderr_output:
            return True
        time.sleep(10)

    log_queue.put("Failed to download nodectl after multiple attempts.\n")
    return False

def check_winscp_and_putty_installed():
    if os.name != 'nt':
        return None
    try:
        # Check for WinSCP installation
        winscp_check = subprocess.check_output(
            'reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\winscp3_is1" /v InstallLocation',
            shell=True,
            text=True
        )
        winscp_path_match = re.search(r"InstallLocation\s+REG_SZ\s+(.+)", winscp_check)
        if winscp_path_match:
            winscp_path = winscp_path_match.group(1).strip()
        else:
            winscp_path = None

        # Check for PuTTY installation
        putty_check = subprocess.check_output(
            'reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\SimonTatham\\PuTTY64"',
            shell=True,
            text=True
        )

        if winscp_path and "PuTTY64" in putty_check:
            return winscp_path
        else:
            return None
    except subprocess.CalledProcessError as e:
        return None

def get_winscp_path():
    if os.name != 'nt':
        return None

    try:
        winscp_check = subprocess.check_output(
            'reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\winscp3_is1" /v InstallLocation',
            shell=True,
            text=True
        )
        winscp_path_match = re.search(r"InstallLocation\s+REG_SZ\s+(.+)", winscp_check)
        if winscp_path_match:
            winscp_path = winscp_path_match.group(1).strip()
            return winscp_path
        else:
            return None
    except Exception as e:
        logging.error(f"Failed to fetch WinSCP path: {e}")
        return None

def convert_key_to_ppk(private_key_path, winscp_path, passphrase):
    if os.name != 'nt':
        return private_key_path + '.ppk'

    if winscp_path is None:
        return None

    ppk_path = private_key_path + '.ppk'
    if not os.path.exists(ppk_path):
        # Convert all slashes to backslashes
        private_key_path = private_key_path.replace('/', '\\')
        ppk_path = ppk_path.replace('/', '\\')
        winscp_command = f'"{winscp_path}\\WinSCP.com" /keygen "{private_key_path}" /output="{ppk_path}" -passphrase="{passphrase}"'
        try:
            subprocess.run(winscp_command, check=True, shell=True)
        except subprocess.CalledProcessError:
            return None
    return ppk_path

def export_server_details_to_putty(server_details, ppk_path, node_username):
    if os.name != 'nt':
        return False

    session_name = server_details['server_name'].replace(" ", "_")
    commands = [
        f'reg add "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions\\{session_name}" /v HostName /t REG_SZ /d {server_details["host_ip"]} /f',
        f'reg add "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions\\{session_name}" /v PortNumber /t REG_DWORD /d 22 /f',
        f'reg add "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions\\{session_name}" /v PublicKeyFile /t REG_SZ /d "{ppk_path}" /f',
        f'reg add "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions\\{session_name}" /v Protocol /t REG_SZ /d ssh /f',
        f'reg add "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions\\{session_name}" /v UserName /t REG_SZ /d {node_username} /f'
    ]
    for command in commands:
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to add registry entry: {e}")
            return False
    return True

def export_server_settings_to_putty(server_name, server_ip, ssh_key_name, ssh_passphrase, node_username, log_queue):
    winscp_path = get_winscp_path()
    if not winscp_path:
        log_queue.put("WinSCP installation path not found. Export to PuTTY skipped.\n")
        return

    ssh_key_path = os.path.expanduser(f"~/.ssh/{ssh_key_name}")
    ppk_path = convert_key_to_ppk(ssh_key_path, winscp_path, ssh_passphrase)
    if not ppk_path:
        log_queue.put("Failed to create the PPK file. Export to PuTTY skipped.\n")
        return

    server_details = {
        'server_name': server_name,
        'host_ip': server_ip,
        'ssh_key_name': ssh_key_name
    }

    success = export_server_details_to_putty(server_details, ppk_path, node_username)
    if success:
        log_queue.put("Server details exported to PuTTY successfully.\n")
    else:
        log_queue.put("Failed to export server details to PuTTY.\n")

def install_nodectl_thread(api_key, server_name, ssh_key, log_queue, ssh_passphrase, node_userpass,
                           p12_passphrase, p12_file, node_username, network, nodectl_version,
                           parent_window, create_shortcuts, export_to_putty):
    try:
        log_queue.put("\nStarting nodectl installation process...\n\n")
        nodeid = None

        log_queue.put(f"Fetching details for droplet '{server_name}'...\n")
        droplets_response = requests.get(
            'https://api.digitalocean.com/v2/droplets?per_page=200',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        )
        droplets = droplets_response.json().get('droplets', []) if droplets_response.status_code == 200 else []
        server = next((d for d in droplets if d.get('name', '').lower() == server_name.lower()), None)
        if not server:
            log_queue.put("Error: Droplet not found.\n")
            return

        server_ip = None
        for net in server.get("networks", {}).get("v4", []):
            if net.get("type") == "public":
                server_ip = net.get("ip_address")
                break

        if not server_ip:
            log_queue.put("Error: Droplet found but no public IP detected.\n")
            return

        log_queue.put(f"Server IP: {server_ip}\n")

        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        private_key_path = os.path.expanduser(f'~/.ssh/{ssh_key}')
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path, password=ssh_passphrase)

        try:
            log_queue.put(f"Connecting to droplet {server_ip} via SSH...\n")
            client.connect(hostname=server_ip, username='root', pkey=private_key)
            log_queue.put("SSH connection successful.\n")

            stdin, stdout, stderr = client.exec_command('command -v tmux')
            tmux_path = stdout.read().decode('utf-8').strip()
            if not tmux_path:
                log_queue.put("\ntmux not found. Installing tmux...\n")
                cmd = (
                    "sudo DEBIAN_FRONTEND=noninteractive apt-get update 2>/dev/null && "
                    "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y tmux 2>/dev/null"
                )
                stdin, stdout, stderr = client.exec_command(cmd)
                stdout.channel.recv_exit_status()
                err_msg = stderr.read().decode('utf-8').strip()
                if err_msg:
                    filtered_err = "\n".join([line for line in err_msg.splitlines() if "debconf" not in line])
                    if filtered_err:
                        log_queue.put(f"tmux install stderr (filtered):\n{filtered_err}\n")
                log_queue.put("tmux installed. Rechecking...\n")
                client.close()
                client.connect(hostname=server_ip, username='root', pkey=private_key)
                stdin, stdout, stderr = client.exec_command('command -v tmux')
                tmux_path = stdout.read().decode('utf-8').strip()
                if not tmux_path:
                    log_queue.put("ERROR: tmux still not found after installation. Aborting.\n")
                    return
                else:
                    log_queue.put(f"tmux installed at: {tmux_path}\n")
            else:
                log_queue.put(f"tmux already installed at {tmux_path}\n")

            # Check if nodectl is already installed.
            stdin, stdout, stderr = client.exec_command('test -f /usr/local/bin/nodectl && echo found')
            if 'found' in stdout.read().decode('utf-8'):
                log_queue.put("nodectl is already installed on this droplet.\n")
                return

            log_queue.put("nodectl not found. Proceeding with installation...\n")

            if not download_nodectl(client, nodectl_version, log_queue):
                return

            verify_command = (
                "if [ -x /usr/local/bin/nodectl ]; then echo 'nodectl is installed and executable'; "
                "else echo 'nodectl download failed'; fi"
            )
            stdin, stdout, stderr = client.exec_command(verify_command)
            verify_output = stdout.read().decode('utf-8')
            if "nodectl is installed and executable" in verify_output:
                log_queue.put("nodectl verified as downloaded and executable.\n")
            else:
                log_queue.put("nodectl download failed. Please check the logs for details.\n")
                return

            client.close()
            client.connect(hostname=server_ip, username='root', pkey=private_key)

            # Upload P12 file if provided.
            if p12_file:
                log_queue.put(f"Uploading P12 file: {p12_file} to /root/\n")
                sftp = client.open_sftp()
                sftp.put(p12_file, f'/root/{os.path.basename(p12_file)}')
                sftp.close()
                log_queue.put("P12 file uploaded successfully.\n")

            client.close()
            client.connect(hostname=server_ip, username='root', pkey=private_key)

            node_userpass_escaped = node_userpass.replace('$', '\\$')
            p12_passphrase_escaped = p12_passphrase.replace('$', '\\$')

            if network in ["mainnet", "testnet"]:
                nprofile = "dag-l0"
            elif network == "integrationnet":
                nprofile = "intnet-l0"
            elif network == "dor-metagraph-mainnet":
                nprofile = "dor-dl1"
            else:
                nprofile = "error-l0"

            if not tmux_path:
                tmux_path = "/usr/bin/tmux"

            nodectl_install_command = (
                f"{tmux_path} new-session -d -s nodectl_install \""
                f"{tmux_path} resize-window -t nodectl_install -x 120 -y 40; "
                f"sudo /usr/local/bin/nodectl install --quick-install "
                f"--user '{node_username}' "
                f"--user-password '{node_userpass_escaped}' "
                f"--p12-passphrase '{p12_passphrase_escaped}' "
                f"--cluster-config '{network}' "
            )
            if p12_file:
                nodectl_install_command += f"--p12-migration-path '/root/{os.path.basename(p12_file)}' "
            nodectl_install_command += f"--skip-system-validation --confirm; sudo nodectl nodeid -p {nprofile}\""

            log_queue.put(f"\nExecuting nodectl install...\n")
            stdin, stdout, stderr = client.exec_command(nodectl_install_command)
            stdout_output = stdout.read().decode('utf-8')
            stderr_output = stderr.read().decode('utf-8')
            if stdout_output:
                log_queue.put(f"STDOUT:\n{stdout_output}\n")
            if stderr_output:
                log_queue.put(f"STDERR:\n{stderr_output}\n")

            installation_complete = False
            log_file_path = None
            possible_log_paths = [
                "/var/tessellation/nodectl/logs/nodectl.log",
                "/var/tessellation/nodectl/nodectl.log"
            ]
            log_queue.put("Waiting for the nodectl.log file to start processing...\n")
            while not log_file_path:
                for path in possible_log_paths:
                    stdin, stdout, stderr = client.exec_command(f'test -f {path} && echo exists')
                    if 'exists' in stdout.read().decode('utf-8'):
                        log_file_path = path
                        log_queue.put(f"nodectl.log file detected at {log_file_path}.\n")
                        break
                if not log_file_path:
                    time.sleep(2)
            
            def tail_log():
                nonlocal installation_complete
                local_client = paramiko.SSHClient()
                local_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                local_client.connect(hostname=server_ip, username='root', pkey=private_key)
                stdin, stdout, stderr = local_client.exec_command(f'tail -f {log_file_path}')
                for line in iter(stdout.readline, ""):
                    log_queue.put(line)
                    if "INFO : Installation complete !!!" in line:
                        log_queue.put("\nnodectl installation process completed.\n\n")
                        installation_complete = True
                        break
                local_client.exec_command(f"{tmux_path} kill-session -t nodectl_install")
                local_client.close()
            tail_thread = threading.Thread(target=tail_log)
            tail_thread.daemon = True
            tail_thread.start()
            tail_thread.join()

            if installation_complete:
                remote_home = f"/home/{node_username}"
                if not remote_home:
                    log_queue.put("Unable to determine remote home directory.\n")
                    return

                p12_search_command = f"ls {remote_home}/tessellation/*.p12 2>/dev/null"
                stdin, stdout, stderr = client.exec_command(p12_search_command)
                remote_files = stdout.read().decode('utf-8').strip().splitlines()
                if not remote_files or remote_files[0] == "":
                    log_queue.put(f"No P12 file found in {remote_home}/tessellation on the remote server.\n")
                    return
                p12_basename = os.path.basename(remote_files[0])
                
                stdin, stdout, stderr = client.exec_command("which xxd")
                xxd_path = stdout.read().decode().strip()
                if xxd_path:
                    xxd_cmd = "xxd -p -c 256"
                else:
                    xxd_cmd = "hexdump -ve '1/1 \"%02x\"'"

                openssl_cmd = (
                    f"openssl pkcs12 -in {remote_home}/tessellation/{p12_basename} -passin pass:'{p12_passphrase}' -nodes -nocerts 2>/dev/null | "
                    "openssl ec -pubout -outform DER 2>/dev/null | tail -c 64 | " + xxd_cmd
                )
                stdin, stdout, stderr = client.exec_command(openssl_cmd)
                nodeid_output = stdout.read().decode('utf-8').strip()
                err_output = stderr.read().decode('utf-8').strip()
                if err_output:
                    log_queue.put(f"Error extracting node ID: {err_output}\n")
                if nodeid_output:
                    nodeid = nodeid_output
                    log_queue.put(f"\nNode ID extracted: {nodeid}\n\n")
                else:
                    log_queue.put("Failed to extract Node ID.\n")
                    return
            else:
                log_queue.put("nodectl installation did not complete as expected.\n")
                return

            username = node_username
            ssh_key_path = os.path.expanduser(f'~/.ssh/{ssh_key}')
            ssh_command = f'ssh -i "{ssh_key_path}" {username}@{server_ip}'
            sftp_command = f'sftp -i "{ssh_key_path}" {username}@{server_ip}'
            ssh_config_file = save_server_info(server_name, server_ip, ssh_key_path, username, network)

            if create_shortcuts:
                if os.name == 'nt':
                    log_queue.put("Creating Desktop Shortcuts...\n")
                    create_windows_shortcuts(server_name, ssh_command, sftp_command)
                else:
                    log_queue.put("Creating Desktop Shortcuts...\n")
                    create_unix_aliases(server_name, ssh_command, sftp_command)

            if export_to_putty and os.name == 'nt':
                log_queue.put("Exporting server details to PuTTY...\n")
                export_server_settings_to_putty(server_name, server_ip, ssh_key, ssh_passphrase, node_username, log_queue)

            def show_message():
                message_window = tk.Toplevel(parent_window)
                message_window.title("Installation Complete")
                main_message = (f"nodectl has completed installing successfully on droplet '{server_name}'.\n\n"
                                f"Server information updated in:\n{ssh_config_file}\n\n")
                if nodeid:
                    main_message += "Node ID:\nClick inside the box below to copy."
                message_label = tk.Label(message_window, text=main_message, justify="left", wraplength=400)
                message_label.pack(pady=10)
                if nodeid:
                    nodeid_entry = tk.Entry(message_window, width=70, font=("Arial", 12))
                    nodeid_entry.insert(0, nodeid)
                    nodeid_entry.config(state="readonly")
                    nodeid_entry.pack(pady=10)
                    def copy_nodeid(event):
                        parent_window.clipboard_clear()
                        parent_window.clipboard_append(nodeid)
                        parent_window.update()
                        tk.messagebox.showinfo("Copied", "Node ID has been copied to the clipboard.")
                    nodeid_entry.bind("<Button-1>", copy_nodeid)
                buttons_frame = tk.Frame(message_window)
                buttons_frame.pack(pady=20)
                def open_server_info():
                    if os.name == 'nt':
                        os.startfile(ssh_config_file)
                    else:
                        if platform.system() == "Darwin":
                            subprocess.call(['open', ssh_config_file])
                        elif platform.system() == "Linux":
                            subprocess.call(['xdg-open', ssh_config_file])
                    message_window.destroy()
                yes_button = tk.Button(buttons_frame, text="Open Server Config File", command=open_server_info)
                yes_button.pack(side="left", padx=10)
                close_button = tk.Button(buttons_frame, text="Close", command=message_window.destroy)
                close_button.pack(side="right", padx=10)
                message_window.geometry("+%d+%d" % (parent_window.winfo_rootx() + 50, parent_window.winfo_rooty() + 50))
                message_window.transient(parent_window)
                message_window.grab_set()
                parent_window.wait_window(message_window)
            show_message()

        except Exception as e:
            log_queue.put(f"SSH operation failed: {str(e)}\n")
        finally:
            client.close()

    except Exception as e:
        log_queue.put(f"Exception during nodectl installation: {str(e)}\n")

def process_log_queue(status_text, log_queue):
    def check_log_queue():
        try:
            while True:
                message = log_queue.get_nowait()
                status_text.insert(tk.END, message)
                status_text.see(tk.END)
        except queue.Empty:
            pass
        status_text.after(100, check_log_queue)
    
    check_log_queue()

def export_to_putty(api_key, server_name):
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    server = next((srv for srv in fetch_data(api_key)[0] if srv['name'] == server_name), None)
    if not server:
        messagebox.showerror("Error", "Server not found.")
        return

    server_ip = server['public_net']['ipv4']['ip']
    ssh_key = server['ssh_keys'][0]

    putty_cmd = f"putty -i ~/.ssh/{ssh_key} root@{server_ip}"
    subprocess.run(putty_cmd, shell=True)
    messagebox.showinfo("Success", f"Exported to PuTTY for server '{server_name}'.")

def create_app_window(api_key):
    # Ensure the local .ssh directory exists.
    ssh_dir = os.path.expanduser("~/.ssh")
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir)
    
    config = load_config()
    firewalls, server_types, locations, servers = fetch_data(api_key)
    ssh_keys = fetch_ssh_keys(api_key)

    # Add any local SSH keys that haven't been imported.
    local_ssh_keys = [f for f in os.listdir(os.path.expanduser("~/.ssh")) if f.endswith('.pub')]
    local_ssh_keys = [os.path.splitext(f)[0] for f in local_ssh_keys]
    ssh_names_on_digitalocean = [ssh['name'] for ssh in ssh_keys]
    for local_key in local_ssh_keys:
        if local_key not in ssh_names_on_digitalocean:
            ssh_keys.append({'name': f"Local: {local_key}", 'local_only': True})

    if os.name == 'nt':
        export_to_putty_var = tk.BooleanVar()
    else:
        export_to_putty_var = None

    # Set up the main application window.
    app = tk.Toplevel()
    app.title("Digital Ocean Cloud Management Tool")
    app.geometry("825x535")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("CreateServer.TButton", foreground="white", background="#00008B", font=("Helvetica", 12, "bold"))
    style.map("CreateServer.TButton", background=[("active", "#000000"), ("!active", "#00008B")])
    style.configure("InstallNodectl.TButton", foreground="white", background="dark green", font=("Helvetica", 12, "bold"))
    style.map("InstallNodectl.TButton", background=[("active", "#000000"), ("!active", "dark green")])
    app.minsize(815, 535)

    menu_bar = tk.Menu(app)
    app.config(menu=menu_bar)
    create_shortcuts_var = tk.BooleanVar()

    # File menu for import/export.
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)

    def import_config():
        file_path = tk.filedialog.askopenfilename(filetypes=[("Config Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "r") as file_to_import:
                new_config = {}
                for line in file_to_import:
                    key, value = line.strip().split(' = ')
                    new_config[key] = value
            server_name_entry.delete(0, tk.END)
            server_name_entry.insert(0, new_config.get("server_name", ""))
            location_dropdown.set(new_config.get("location", ""))
            firewall_dropdown.set(new_config.get("firewall", ""))
            selected_firewall.set(new_config.get("firewall", ""))
            ssh_dropdown.set(new_config.get("ssh_key", ""))
            selected_ssh.set(new_config.get("ssh_key", ""))
            selected_specs = new_config.get("specs", "")
            if selected_specs:
                for item in specs_tree.get_children():
                    if specs_tree.item(item)['values'][0] == selected_specs:
                        specs_tree.selection_set(item)
                        break
            adjust_column_widths(specs_tree)

    def export_config():
        file_path = tk.filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Config Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            config_data = {
                "server_name": server_name_entry.get(),
                "location": selected_location_var.get(),
                "firewall": selected_firewall.get(),
                "ssh_key": selected_ssh.get(),
                "specs": spec_slug_mapping.get(specs_tree.selection()[0], "") if specs_tree.selection() else ""
            }
            with open(file_path, "w") as file_to_export:
                for key, value in config_data.items():
                    file_to_export.write(f"{key} = {value}\n")

    file_menu.add_command(label="Import Config", command=import_config)
    file_menu.add_command(label="Export Config", command=export_config)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=app.quit)

    def on_closing():
        config_data = {
            "server_name": server_name_entry.get(),
            "location": selected_location_var.get(),
            "firewall": selected_firewall.get(),
            "ssh_key": selected_ssh.get(),
            "specs": spec_slug_mapping.get(specs_tree.selection()[0], "") if specs_tree.selection() else config.get("specs", "")
        }
        save_config(config_data)

        threads_to_ignore = {'pydevd.Writer', 'pydevd.Reader', 'pydevd.CommandThread', 'pydevd.CheckAliveThread'}
        for thread in threading.enumerate():
            if thread.name not in threads_to_ignore and thread is not threading.main_thread():
                logging.debug(f"Waiting for thread {thread.name} to finish.")
                try:
                    thread.join(timeout=1)
                except RuntimeError as e:
                    logging.debug(f"Skipping thread {thread.name}: {e}")

        root.quit()
        root.destroy()
        sys.exit(0)

    app.protocol("WM_DELETE_WINDOW", on_closing)

    selected_firewall = tk.StringVar(value=config.get("firewall", ""))
    selected_ssh = tk.StringVar(value=config.get("ssh_key", ""))
    selected_network_var = tk.StringVar(value="")
    node_username_var = tk.StringVar(value="nodeadmin")

    def update_firewall_buttons(*args):
        selected_firewall_name = selected_firewall.get()
        if selected_firewall_name in [fw['name'] for fw in firewalls]:
            new_button.pack_forget()
            edit_button.pack(side=tk.LEFT, padx=5)
        else:
            edit_button.pack_forget()
            new_button.pack(side=tk.LEFT, padx=5)

    notebook = ttk.Notebook(app)
    notebook.pack(fill='both', expand=True)

    create_server_tab = tk.Frame(notebook)
    install_nodectl_tab = tk.Frame(notebook)
    notebook.add(create_server_tab, text="Create Server")
    notebook.add(install_nodectl_tab, text="Install nodectl")

    # Create Server Tab
    tk.Label(create_server_tab, text="Server Name:").grid(row=0, column=1, padx=5, pady=5, sticky='w')
    server_name_entry = tk.Entry(create_server_tab, width=33)
    Tooltip(server_name_entry, "Type the name for your new server.\n(No spaces or special characters).")
    server_name_entry.grid(row=0, column=1, padx=(100, 0), pady=10, sticky='w')
    server_name_entry.insert(0, config.get("server_name", ""))

    tk.Label(create_server_tab, text="Location:").grid(row=1, column=1, padx=5, pady=5, sticky='w')
    selected_location_var = tk.StringVar(value=config.get("location", ""))
    locations_sorted = sorted(locations, key=lambda loc: loc.get('name', ''))
    location_dropdown = ttk.Combobox(create_server_tab, textvariable=selected_location_var,
                                     values=[f"{loc['slug']} - {loc['name']}" for loc in locations_sorted],
                                     width=30)
    Tooltip(location_dropdown, "Select the location for your new server.\nThe available specs for that location will be visible below.")
    location_dropdown.grid(row=1, column=1, padx=(100, 0), pady=10, sticky='w')
    location_dropdown.set(config.get("location", ""))

    tk.Label(create_server_tab, text="Distribution:").grid(row=3, column=1, padx=5, pady=5, sticky='w')
    distribution_var = tk.StringVar(value="ubuntu-22.04")
    distribution_dropdown = ttk.Combobox(create_server_tab, textvariable=distribution_var,
                                         values=["ubuntu-22.04", "ubuntu-24.04", "debian-12"],
                                         width=30)
    distribution_dropdown.grid(row=3, column=1, padx=(100, 0), pady=10, sticky='w')
    distribution_dropdown.set("ubuntu-22.04")

    # ------------------ SPECS (Droplet Sizes) ------------------
    specs_frame = tk.Frame(create_server_tab)
    specs_frame.grid(row=2, column=1, columnspan=3, padx=10, pady=10, sticky='nsew')

    # New columns: TYPE, BRAND, vCPUs, RAM, DISK, PRICE
    columns = ("type", "brand", "vcpus", "ram", "disk", "price")
    specs_tree = ttk.Treeview(specs_frame, columns=columns, show="headings", height=10)
    specs_tree.grid(row=0, column=0, sticky='nsew')
    v_scrollbar = tk.Scrollbar(specs_frame, orient=tk.VERTICAL, command=specs_tree.yview)
    v_scrollbar.grid(row=0, column=1, sticky='ns')
    h_scrollbar = tk.Scrollbar(specs_frame, orient=tk.HORIZONTAL, command=specs_tree.xview)
    h_scrollbar.grid(row=1, column=0, sticky='ew')
    specs_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
    specs_frame.grid_columnconfigure(0, weight=1)
    specs_frame.grid_rowconfigure(0, weight=1)

    # Set up headings (using a helper for sorting).
    def treeview_sort_column(tv, col, reverse):
        def parse_size(size_str):
            if 'GB' in size_str:
                return float(size_str.replace('GB', ''))
            elif 'TB' in size_str:
                return float(size_str.replace('TB', '')) * 1024
            return 0
        if col in ['vcpus']:
            l = [(int(tv.set(k, col)), k) for k in tv.get_children('')]
        elif col in ['ram', 'disk']:
            l = [(parse_size(tv.set(k, col)), k) for k in tv.get_children('')]
        elif col == 'price':
            l = [(float(tv.set(k, col)[1:].split('/')[0]), k) for k in tv.get_children('')]
        else:
            l = [(tv.set(k, col), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))

    for col in columns:
        specs_tree.heading(col, text=col.upper(), command=lambda _col=col: treeview_sort_column(specs_tree, _col, False))

    def adjust_column_widths(tree):
        for col in tree["columns"]:
            max_width = tkFont.Font().measure(col.upper())
            for item in tree.get_children():
                text = str(tree.set(item, col))
                max_width = max(max_width, tkFont.Font().measure(text))
            tree.column(col, width=max_width + 20, stretch=False)

    adjust_column_widths(specs_tree)
    specs_frame.config(width=400)

    # Global dictionary to map Treeview item IDs to their original DO size slugs.
    global spec_slug_mapping
    spec_slug_mapping = {}

    # A label under the specs Treeview to show the selected spec's slug.
    spec_slug_label = tk.Label(specs_frame, text="Selected Specs: None", anchor="w")
    spec_slug_label.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 0))

    # The update_specs function builds the specs list from the DO sizes.
    def update_specs(*args):
        # logger.debug("Updating specs with new TYPE and BRAND columns.")
        # (We do not re-fetch sizes here so that we use the originally loaded sizes.)
        selected_loc = selected_location_var.get().strip()
        region_filter = selected_loc.split(" - ")[0].strip() if selected_loc else None
        # logger.debug("Region filter: %s", region_filter)

        # Helper: map a slug (and description) to TYPE and BRAND.
        def map_slug_to_type_and_brand(slug: str, desc: str) -> (str, str):
            if slug.startswith("s-"):
                type_name = "Shared CPU"
                if slug.endswith("-amd") or "amd" in desc:
                    brand = "Premium AMD"
                elif slug.endswith("-intel") or "intel" in desc:
                    brand = "Premium Intel"
                else:
                    brand = "Standard"
            elif slug.startswith("g-"):
                type_name = "General Purpose"
                if "-intel" in slug or "intel" in desc:
                    brand = "Premium Intel"
                elif "-amd" in slug or "amd" in desc:
                    brand = "Premium AMD"
                else:
                    brand = "Regular Intel"
            elif slug.startswith("c-") or slug.startswith("c2-"):
                type_name = "CPU-Optimized"
                if "-intel" in slug or "intel" in desc:
                    brand = "Premium Intel"
                elif "-amd" in slug or "amd" in desc:
                    brand = "Premium AMD"
                else:
                    brand = "Regular Intel"
            elif slug.startswith("m-") or slug.startswith("m3-"):
                type_name = "Memory-Optimized"
                if "-intel" in slug or "intel" in desc:
                    brand = "Premium Intel"
                elif "-amd" in slug or "amd" in desc:
                    brand = "Premium AMD"
                else:
                    brand = "Regular Intel"
            elif slug.startswith("so-") or slug.startswith("so1-"):
                type_name = "Storage-Optimized"
                if "-intel" in slug or "intel" in desc:
                    brand = "Premium Intel"
                elif "-amd" in slug or "amd" in desc:
                    brand = "Premium AMD"
                else:
                    brand = "Regular Intel"
            else:
                type_name, brand = None, None
            return type_name, brand

        # Clear the mapping dictionary.
        spec_slug_mapping.clear()
        available_specs = []
        for spec in server_types:
            if region_filter and region_filter not in spec.get("regions", []):
                continue
            orig_slug = spec.get("slug", "")
            slug = orig_slug.lower()
            desc = spec.get("description", "").lower()
            type_name, brand = map_slug_to_type_and_brand(slug, desc)
            if type_name is None:
                continue
            vcpus = spec.get("vcpus", 0)
            vcpus_display = f"{vcpus} vCPU"
            memory_mb = spec.get("memory", 0)
            ram_display = f"{memory_mb/1024:.1f}GB" if memory_mb >= 1024 else f"{memory_mb}MB"
            disk = spec.get("disk", 0)
            disk_display = f"{disk}GB"
            price = spec.get("price_monthly", 0)
            price_display = f"${price:.2f}/mo"
            display_data = (type_name, brand, vcpus_display, ram_display, disk_display, price_display)
            available_specs.append((display_data, orig_slug))
        # logger.debug("Available specs after processing: %s", available_specs)
        available_specs.sort(key=lambda x: float(x[0][5].replace("$", "").split("/")[0]))
        for item in specs_tree.get_children():
            specs_tree.delete(item)
        for display_data, orig_slug in available_specs:
            item_id = specs_tree.insert("", "end", values=display_data)
            spec_slug_mapping[item_id] = orig_slug
        adjust_column_widths(specs_tree)
    # Bind the region dropdown changes to update_specs.
    selected_location_var.trace('w', update_specs)
    update_specs()

    # Bind selection event on the specs tree to update the slug label.
    def on_spec_select(event):
        selected_items = specs_tree.selection()
        if selected_items:
            item_id = selected_items[0]
            slug_val = spec_slug_mapping.get(item_id, "N/A")
            spec_slug_label.config(text=f"Selected Specs: {slug_val}")
        else:
            spec_slug_label.config(text="Selected Spec Slug: None")
    specs_tree.bind("<<TreeviewSelect>>", on_spec_select)
    # ------------------ End SPECS ------------------

    # Firewall dropdown.
    tk.Label(create_server_tab, text="Firewall:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
    firewall_dropdown = ttk.Combobox(create_server_tab, textvariable=selected_firewall,
                                     values=[fw['name'] for fw in firewalls], width=25)
    firewall_dropdown.set(config.get("firewall", ""))
    firewall_dropdown.grid(row=0, column=2, padx=(100, 0), pady=10, sticky='w')
    firewall_buttons_frame = tk.Frame(create_server_tab)
    firewall_buttons_frame.grid(row=0, column=3, padx=10, pady=10, sticky='e')
    new_button = tk.Button(firewall_buttons_frame, text="New", command=lambda: create_edit_firewall_window(api_key, {}, firewall_dropdown), width=10)
    edit_button = tk.Button(firewall_buttons_frame, text="Edit", command=lambda: edit_firewall(api_key, selected_firewall.get(), firewall_dropdown), width=10)
    delete_button = tk.Button(firewall_buttons_frame, text="Delete", command=lambda: delete_firewall(api_key, selected_firewall.get(), firewall_dropdown, selected_firewall), width=10)
    delete_button.pack(side=tk.LEFT, padx=5)
    update_firewall_buttons()
    selected_firewall.trace("w", update_firewall_buttons)

    # SSH Key dropdown.
    tk.Label(create_server_tab, text="SSH Key:").grid(row=1, column=2, padx=5, pady=5, sticky='w')
    ssh_dropdown = ttk.Combobox(create_server_tab, textvariable=selected_ssh,
                                values=[ssh['name'] for ssh in ssh_keys], width=25)
    ssh_dropdown.set(config.get("ssh_key", ""))
    ssh_dropdown.grid(row=1, column=2, padx=(100, 0), pady=10, sticky='w')
    ssh_buttons_frame = tk.Frame(create_server_tab)
    ssh_buttons_frame.grid(row=1, column=3, padx=10, pady=10, sticky='e')
    def update_ssh_buttons(*args):
        for widget in ssh_buttons_frame.winfo_children():
            widget.destroy()
        button_frame = tk.Frame(ssh_buttons_frame)
        button_frame.pack(side=tk.LEFT, padx=5)
        delete_button = tk.Button(button_frame, text="Delete", command=lambda: delete_ssh_key(api_key, selected_ssh.get(), ssh_dropdown, selected_ssh, update_ssh_buttons), width=10)
        delete_button.pack(side=tk.LEFT)
        if selected_ssh.get().startswith("Local: "):
            import_button = tk.Button(button_frame, text="Import", command=lambda: import_ssh(api_key, selected_ssh.get().replace("Local: ", ""), ssh_dropdown), width=10)
            import_button.pack(side=tk.RIGHT, padx=(10, 0))
        else:
            new_button = tk.Button(button_frame, text="New", command=lambda: create_ssh_key(api_key, selected_ssh.get(), None, ssh_dropdown), width=10)
            if selected_ssh.get() in [ssh['name'] for ssh in ssh_keys]:
                new_button.config(state=tk.DISABLED)
            else:
                delete_button.config(state=tk.DISABLED)
            new_button.pack(side=tk.RIGHT, padx=(10, 0))
    selected_ssh.trace("w", update_ssh_buttons)
    update_ssh_buttons()

    # Create Server button callback.
    selected_server_var = tk.StringVar()
    server_dropdown = ttk.Combobox(install_nodectl_tab, textvariable=selected_server_var,
                                   values=[srv['name'] for srv in servers], width=25)
    server_dropdown.grid(row=0, column=1, padx=(5, 10), pady=10, ipadx=5, sticky='ew')
    def create_server_button_click():
        if not specs_tree.selection():
            messagebox.showerror("Error", "Please select a server spec.")
            return
        server_name = server_name_entry.get()
        firewall_name = selected_firewall.get()
        ssh_key_name = selected_ssh.get()
        if not firewall_name:
            firewall_name = f"{server_name}-fw"
            selected_firewall.set(firewall_name)
            firewall_dropdown.set(firewall_name)
        if not ssh_key_name:
            ssh_key_name = f"{server_name}-ssh"
            selected_ssh.set(ssh_key_name)
            ssh_dropdown.set(ssh_key_name)
        # Ensure a firewall exists; if not, create one.
        firewalls, server_types, locations, servers = fetch_data(api_key)
        firewall = next((fw for fw in firewalls if fw['name'] == firewall_name), None)
        if not firewall:
            firewall_id = create_new_firewall_with_defaults(api_key, firewall_name)
            if not firewall_id:
                messagebox.showerror("Error", "Failed to create a new firewall.")
                return
        # Retrieve the size slug from the mapping dictionary using the selected specs row.
        selected_item = specs_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a server spec.")
            return
        size_slug = spec_slug_mapping.get(selected_item[0])
        if not size_slug:
            messagebox.showerror("Error", "Failed to retrieve the selected server spec slug.")
            return
        region_slug = selected_location_var.get().split(" - ")[0].strip()
        # Call create_server with the correct parameters.
        create_server(api_key,
                      server_name,
                      size_slug,
                      distribution_var.get(),
                      region_slug,
                      selected_ssh.get(),
                      ssh_dropdown, 
                      create_server_button)
        # Refresh droplet list.
        _, _, _, servers = fetch_data(api_key)
        server_names = [srv['name'] for srv in servers]
        server_dropdown['values'] = server_names
        if server_names:
            selected_server_var.set(server_name)

    create_server_button = ttk.Button(create_server_tab, text="Create Server",
                                      command=create_server_button_click,
                                      style="CreateServer.TButton", width=20)
    create_server_button.grid(row=10, column=1, columnspan=3, padx=15, pady=10, sticky='se')

    create_server_tab.grid_columnconfigure(0, weight=2)
    create_server_tab.grid_columnconfigure(1, weight=3)
    create_server_tab.grid_columnconfigure(2, weight=1)
    create_server_tab.grid_columnconfigure(3, weight=1)
    create_server_tab.grid_rowconfigure(2, weight=1)
    # ------------------ End Create Server Tab ------------------

    # Install nodectl Tab (unchanged) …
    tk.Label(install_nodectl_tab, text="Select Server:").grid(row=0, column=0, padx=(10, 5), pady=10, sticky='w')
    selected_server_var = tk.StringVar()
    server_dropdown = ttk.Combobox(install_nodectl_tab, textvariable=selected_server_var,
                                   values=[srv['name'] for srv in servers], width=25)
    server_dropdown.grid(row=0, column=1, padx=(5, 10), pady=10, ipadx=5, sticky='ew')
    selected_server_var.trace("w", lambda *args: on_server_select(selected_server_var, status_text, api_key, *args))
    tk.Label(install_nodectl_tab, text="Select SSH Key:").grid(row=0, column=2, padx=(10, 5), pady=10, sticky='e')
    ssh_dropdown2 = ttk.Combobox(install_nodectl_tab, textvariable=selected_ssh,
                                  values=[ssh['name'] for ssh in ssh_keys], width=25)
    ssh_dropdown2.set(config.get("ssh_key", ""))
    ssh_dropdown2.grid(row=0, column=3, padx=(5, 10), pady=10, ipadx=5, sticky='ew')
    selected_ssh.trace("w", lambda *args: ssh_dropdown2.set(selected_ssh.get()))
    tk.Label(install_nodectl_tab, text="Select Network:").grid(row=1, column=0, padx=(10, 5), pady=10, sticky='w')
    selected_network_var = tk.StringVar(value="")
    network_dropdown = ttk.Combobox(install_nodectl_tab, textvariable=selected_network_var,
                                    values=["mainnet", "integrationnet", "testnet", "dor-metagraph-mainnet"], width=25)
    network_dropdown.grid(row=1, column=1, padx=(5, 10), pady=10, ipadx=5, sticky='ew')
    nodectl_versions, latest_nodectl_version = get_available_nodectl_versions()
    tk.Label(install_nodectl_tab, text="nodectl Version:").grid(row=1, column=2, padx=(10, 5), pady=10, sticky='e')
    selected_nodectl_version_var = tk.StringVar(value=latest_nodectl_version)
    nodectl_version_dropdown = ttk.Combobox(install_nodectl_tab, textvariable=selected_nodectl_version_var,
                                             values=nodectl_versions, width=25)
    nodectl_version_dropdown.grid(row=1, column=3, padx=(5, 10), pady=10, ipadx=5, sticky='ew')
    tk.Label(install_nodectl_tab, text="Node Username:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
    node_username_var = tk.StringVar(value="nodeadmin")
    username_entry = tk.Entry(install_nodectl_tab, textvariable=node_username_var, width=35)
    username_entry.grid(row=2, column=1, padx=(5, 10), pady=10, sticky='w')
    install_nodectl_tab.grid_columnconfigure(0, weight=1)
    install_nodectl_tab.grid_columnconfigure(1, weight=1)
    install_nodectl_tab.grid_columnconfigure(2, weight=1)
    install_nodectl_tab.grid_columnconfigure(3, weight=1)

    status_frame = tk.Frame(install_nodectl_tab)
    status_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky='nsew')
    status_text = tk.Text(status_frame, wrap='none', height=13)
    status_text.grid(row=0, column=0, sticky='nsew')
    status_v_scrollbar = tk.Scrollbar(status_frame, orient='vertical', command=status_text.yview)
    status_v_scrollbar.grid(row=0, column=1, sticky='ns')
    status_h_scrollbar = tk.Scrollbar(status_frame, orient='horizontal', command=status_text.xview)
    status_h_scrollbar.grid(row=1, column=0, sticky='ew')
    status_text.configure(yscrollcommand=status_v_scrollbar.set, xscrollcommand=status_h_scrollbar.set)
    status_frame.grid_rowconfigure(0, weight=1)
    status_frame.grid_columnconfigure(0, weight=1)
    install_nodectl_tab.grid_rowconfigure(3, weight=1)

    p12_frame = tk.Frame(install_nodectl_tab)
    p12_frame.grid(row=4, column=0, columnspan=4, padx=10, pady=10, sticky='w')
    tk.Label(p12_frame, text="Import P12 File (Optional):").grid(row=0, column=0, sticky='w')
    p12_file_var = tk.StringVar()
    p12_file_entry = tk.Entry(p12_frame, textvariable=p12_file_var, width=50)
    p12_file_entry.grid(row=0, column=1, padx=(5, 0), sticky='w')
    p12_file_button = tk.Button(p12_frame, text="Browse",
                                command=lambda: p12_file_var.set(filedialog.askopenfilename(filetypes=[("P12 Files", "*.p12"), ("All Files", "*.*")])))
    p12_file_button.grid(row=0, column=2, padx=5, sticky='w')

    if os.name == 'nt':
        create_shortcuts_checkbox = tk.Checkbutton(install_nodectl_tab, text="Create SSH & SFTP Desktop Shortcuts", variable=create_shortcuts_var)
        create_shortcuts_checkbox.grid(row=5, column=1, padx=50, pady=0, sticky='w')
        export_to_putty_checkbox = tk.Checkbutton(install_nodectl_tab, text="Export server settings to PuTTY", variable=export_to_putty_var)
        export_to_putty_checkbox.grid(row=6, column=1, padx=50, pady=0, sticky='w')
        def on_export_to_putty_var_changed(*args):
            if export_to_putty_var.get():
                winscp_path = check_winscp_and_putty_installed()
                if not winscp_path:
                    if messagebox.askyesno("Install Required Software", "PuTTY and/or WinSCP are not installed. Do you want to install them now?"):
                        webbrowser.open("https://www.putty.org")
                        webbrowser.open("https://winscp.net/eng/download.php")
                        messagebox.showinfo("Installation", "Please install PuTTY and WinSCP, then click OK to continue.")
                        winscp_path = check_winscp_and_putty_installed()
                        if not winscp_path:
                            messagebox.showerror("Installation Failed", "PuTTY and/or WinSCP are still not installed. Export to PuTTY will be disabled.")
                            export_to_putty_var.set(False)
                    else:
                        export_to_putty_var.set(False)
        export_to_putty_var.trace_add('write', on_export_to_putty_var_changed)

    install_button = ttk.Button(install_nodectl_tab, text="Install nodectl",
                                  command=lambda: start_install_nodectl(api_key,
                                                                        selected_server_var.get(),
                                                                        selected_ssh.get(),
                                                                        status_text,
                                                                        p12_file_var.get(),
                                                                        node_username_var.get(),
                                                                        selected_network_var.get(),
                                                                        selected_nodectl_version_var.get(),
                                                                        app, create_shortcuts_var, export_to_putty),
                                  style="InstallNodectl.TButton", width=20)
    install_button.grid(row=6, column=0, columnspan=4, padx=25, pady=10, sticky='se')

    # Finally, start the mainloop.
    app.mainloop()
        
def validate_api_key(api_key):
    """
    Validates the DigitalOcean API key by querying the /v2/account endpoint.
    
    Parameters:
      - api_key: Your DigitalOcean API token.
      
    Returns:
      True if the API key is valid; False otherwise.
    """
    
    # logger.debug("Entering validate_api_key with api_key: %s", api_key)
    headers = {'Authorization': f'Bearer {api_key}'}
    url = "https://api.digitalocean.com/v2/account"
    try:
        response = requests.get(url, headers=headers)
        # logger.debug("Response status code: %s", response.status_code)
        # logger.debug("Response text: %s", response.text)
        
        if response.status_code == 200:
            # logger.debug("API key validated successfully.")
            return True
        elif response.status_code == 401:
            messagebox.showerror("Invalid API Key", 
                "The API key provided is invalid or unauthorized. Please check your token.")
            # logger.error("API key validation failed: 401 Unauthorized")
            return False
        else:
            messagebox.showerror("Validation Failed", 
                f"Unexpected response code: {response.status_code}\nResponse: {response.text}")
            # logger.error("Unexpected response: %s", response.text)
            return False
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"An error occurred during API key validation: {e}")
        # logger.error("Exception during API key validation: %s", e)
        return False

def open_link(url):
    import webbrowser
    webbrowser.open(url)

def prompt_api_key():
    global root
    root = tk.Tk()
    root.title("API Key Input")
    root.configure(bg="#333333")

    window_width = 375
    window_height = 230

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    position_x = (screen_width // 2) - (window_width // 2)
    position_y = (screen_height // 3) - (window_height // 2)

    root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Custom.TButton", foreground="white", background="#00008B", font=("Helvetica", 12, "bold"))
    style.map("Custom.TButton", background=[("active", "#000000"), ("!active", "#00008B")])

    instructions_frame = tk.Frame(root, bg="#333333")
    instructions_frame.grid(row=0, column=0, columnspan=2, pady=(10, 5), padx=10, sticky="nsew")

    description_label = tk.Label(
        instructions_frame, 
        text="To manage your cloud resources with DOCloud, you'll need a Read/Write API key from your DigitalOcean account:", 
        bg="#333333", fg="white", wraplength=300, font=("Helvetica", 10), justify="center"
    )
    description_label.pack()

    def open_link(event):
        import webbrowser
        webbrowser.open("https://docs.digitalocean.com/reference/api/create-personal-access-token/")

    link_label = tk.Label(
        instructions_frame, 
        text="Create a DigitalOcean API Key", 
        fg="lightblue", bg="#333333", cursor="hand2", font=("Helvetica", 10, "underline")
    )
    link_label.pack(pady=(5, 0))
    link_label.bind("<Button-1>", open_link)
    Tooltip(link_label, "https://docs.digitalocean.com/reference/api/create-personal-access-token/")

    ttk.Label(
        root, 
        text="Paste your DigitalOcean API key below:", 
        background=root['bg'], foreground="white"
    ).grid(row=1, column=0, columnspan=2, pady=(5, 5), padx=(10, 5))

    api_key_entry = ttk.Entry(root, show="*")
    api_key_entry.grid(row=2, column=0, columnspan=2, pady=(5, 5), padx=(10, 10), sticky="ew")
    api_key_entry.focus_set()

    Tooltip(api_key_entry, "Paste the DigitalOcean API Key. DigitalOcean keys usually start with 'dop_v1_'.")

    submit_button = ttk.Button(root, text="Submit", command=lambda: on_submit(api_key_entry.get()), style="Custom.TButton")
    submit_button.grid(row=3, column=0, columnspan=2, pady=(10, 15))
    Tooltip(submit_button, "Click to submit your API Key and start setting up DOCloud.")

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    
    if os.name == "nt":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    def on_submit(api_key):
        valid = api_key.startswith("dop_v1_")            
        if valid:
            global log_window
            log_window = tk.Toplevel(root)
            log_window.title("Dependency Installation Progress")
            log_window.geometry("600x400")

            log_text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD, height=20, width=70)
            log_text.pack(pady=10, padx=10)

            install_required_packages_in_thread(
                log_text,
                lambda: on_installation_complete(root, api_key) if validate_api_key(api_key) else messagebox.showwarning(
                    "Invalid API Key", "The API key provided is invalid or does not have the required permissions."
                )
            )
        else:
            messagebox.showerror("Invalid API Key", "Invalid API key. Please enter a valid API key.")
    
    root.bind('<Return>', lambda event: on_submit(api_key_entry.get()))
    root.mainloop()

# def debug_fetch_data(api_key):
#     firewalls, sizes, regions, droplets = fetch_data(api_key)
    
#     print("=== RAW DATA FROM DIGITALOCEAN API ===")
#     print("\n--- Firewalls ---")
#     print(json.dumps(firewalls, indent=2))
    
#     print("\n--- Droplet Sizes (Server Types) ---")
#     print(json.dumps(sizes, indent=2))
    
#     print("\n--- Regions ---")
#     print(json.dumps(regions, indent=2))
    
#     print("\n--- Droplets ---")
#     print(json.dumps(droplets, indent=2))

if __name__ == "__main__":
    prompt_api_key()
