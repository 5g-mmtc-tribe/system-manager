# config/constants.py
"""
Internal constant settings.
These values are generally fixed and are used across the application.
"""
import os 

# --- Paths and Directories ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(BASE_DIR, "../scripts")
USER_SCRIPT_PATH = os.path.join(BASE_DIR, "../user-scripts")
TOOLS_SCRIPT_PATH = os.path.join(BASE_DIR, "../tools")

#API_DIR = os.path.join(BASE_DIR, "../api")
#JETSON_PATH = os.path.join(API_DIR, "jetson")
#DATA_DIR  = os.path.join(BASE_DIR, "../data")
# for deploiment 
#BASE_PATH: str = os.path.join(DATA_DIR, 'jetson_linux_r35.4.1_aarch64.tbz2')
#ROOTFS_PATH: str = os.path.join(DATA_DIR, 'tegra_linux_sample-root-filesystem_r35.4.1_aarch64.tbz2')
# --- Internal Constants ---
NBD_SIZE = 16384

# --- File used   in create_env_vm  ---

# Define the nbd
CONFIG_DIR = os.path.abspath(os.path.join(BASE_DIR, "../config"))
IP_CONFIG_FILE_PATH = os.path.join(BASE_DIR, "ipconfig.txt")
DHCP_CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "dhcpConfig.txt")

#--- nfs 
ROOT_FS_3274 = "/root/nfsroot-jp-3274"
ROOT_FS_3541 = "/root/nfsroot-jp-3541"