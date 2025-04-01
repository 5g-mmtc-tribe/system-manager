
"""
User configuration settings.

"""

import os

# --- Network Settings ---
HOST_INTERFACE = "eno1"  # Used for switch to the VM (host side)
VM_INTERFACE = "enp6s0"  # Used to check if the VM network is up

# --- Redis Settings ---
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_USER_INDEX = 'UserIdxs'

# -------------------------------
# VPN Settings
# -------------------------------
VPN_NAME = "vm-openvpn-server"

# -------------------------------
# FastAPI Application Settings
# -------------------------------
API_HOST = "localhost"
API_PORT = 5000


# --- Paths and Directories ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))



# -------------------------------
# Configuration File Paths
# -------------------------------
CONFIG_DIR = os.path.abspath(os.path.join(BASE_DIR, "../config"))
SWITCH_CONFIG_PATH = os.path.join(CONFIG_DIR, "switch_config.json")
ACTIVE_USERS_PATH = os.path.join(CONFIG_DIR, "active_users.json")
RESOURCE_JSON_PATH = os.path.join(CONFIG_DIR, "resource.json")
RESSOURCE_CSV_PATH = os.path.join("/home/fs-5gmmtclab/Workspace", "list_devices.csv")

# -- file used in systeme_manager_api --

# -------------------------------
#  NFS Driver Settings
# ------------------------------

DRIVER_3274 =  "rootfs-jp3274.tar.gz"
DRIVER_3541 =  "rootfs-basic-jp3541-noeula-user.tar.gz"
DRIVER_3274_PATH = os.path.join(CONFIG_DIR, "rootfs-jp3274.tar.gz")
DRIVER_3541_PATH  = os.path.join(CONFIG_DIR, "rootfs-basic-jp3541-noeula-user.tar.gz")

BASE_IMAGE_J20_J40 = os.path.join(BASE_DIR, "nbd_jetson_jp3541.img")
NBD_IMAGE_NAME_J20_J40 ="nbd_jetson_jp3541.img"

BASE_IMAGE_J10 = os.path.join(BASE_DIR, "nbd_jetson_jp3274.img")
NBD_IMAGE_NAME_J10 ="nbd_jetson_jp3274.img"
# -------------------------------
# User Script Paths for Jetson from user-scripts
# -------------------------------
USER_SCRIPT_PATH_3274 = "jetson/jp3274/"
USER_SCRIPT_PATH_3271 = "jetson/jp3541/"


# -------------------------------
# Logging Settings
# -------------------------------
LOGS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../logs"))
SYSTEM_MANAGER_LOG_FILE = os.path.join(LOGS_DIR, "system_manager.log")
