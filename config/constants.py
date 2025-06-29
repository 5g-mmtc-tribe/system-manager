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
RPI4_CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "tabhosts-rpi4.conf")
JTX2_CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "tabhosts-jtx2.conf")
#--- nfs 
ROOT_FS_3274 = "/root/nfsroot-jp-3274"
ROOT_FS_3541 = "/root/nfsroot-jp-3541"
ROOT_FS_RPI4 = "/root/nfsroot_rpi4"


# -------------------------------
# User Script Paths for Jetson from user-scripts
# -------------------------------
USER_SCRIPT_PATH_3274 = "jetson/jp3274/"
USER_SCRIPT_PATH_3271 = "jetson/jp3541/"

# nfs script name
JETSON_SETUP_NFS = "nfs_setup.sh"
RPI4_SETUP_NFS = "nfs_rpi4_setup.sh"
# -------------------------------
#  NFS Driver Settings
# ------------------------------
DRIVER_SERVER_IP = "193.55.250.147"
DRIVER_3274 =  "rootfs-jp3274.tar.gz"
DRIVER_3541 =  "rootfs-basic-jp3541-noeula-user.tar.gz"
DRIVER_RPI4 = "core-image-minimal-rpi4-rootfs.tar.bz2"
DRIVER_3274_PATH = os.path.join(CONFIG_DIR, DRIVER_3541 )
DRIVER_3541_PATH  = os.path.join(CONFIG_DIR, DRIVER_3541 )
DRIVER_RPI4_PATH = os.path.join(CONFIG_DIR, DRIVER_RPI4 )
BASE_IMAGE_J20_J40 = os.path.join(BASE_DIR, "nbd_jetson_jp3541.img")
NBD_IMAGE_NAME_J20_J40 ="nbd_jetson_jp3541.img"

BASE_IMAGE_J10 = os.path.join(BASE_DIR, "nbd_jetson_jp3274.img")
NBD_IMAGE_NAME_J10 ="nbd_jetson_jp3274.img"
BASE_IMAGE_JTX = os.path.join(BASE_DIR, "nbd_jetson_jp3274_tx2.img")
NBD_IMAGE_NAME_JTX ="nbd_jetson_jp3274_tx2.img"