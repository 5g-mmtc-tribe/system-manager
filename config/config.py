import logging
import os
from dotenv import load_dotenv

"""
System Manager Configuration Settings
"""

# 1) Identify this file’s directory (i.e. 5g-conf/system_manager)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

root_file_relative = os.path.join("..", "..","5g-conf", "system_manager","dev")
env_file = os.path.join(BASE_DIR,root_file_relative, ".env.dev" )
# If you want to load a production file, replace with ".env.prod"

if os.path.exists(env_file):
    load_dotenv(dotenv_path=env_file)


# --------------------------------------------------------------------------
# Network Settings
# --------------------------------------------------------------------------
HOST_INTERFACE = os.getenv("HOST_INTERFACE", "eno1")  # Used for the switch to the VM (host side)
VM_INTERFACE   = os.getenv("VM_INTERFACE", "enp6s0")  # Used to check if the VM network is up

# --------------------------------------------------------------------------
# Redis Settings
# --------------------------------------------------------------------------
REDIS_HOST       = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT       = int(os.getenv("REDIS_PORT", "6379"))
REDIS_USER_INDEX = os.getenv("REDIS_USER_INDEX", "UserIdxs")

# --------------------------------------------------------------------------
# VPN Settings
# --------------------------------------------------------------------------
VPN_NAME = os.getenv("VPN_NAME", "vm-openvpn-server")

# --------------------------------------------------------------------------
# FastAPI Application Settings
# --------------------------------------------------------------------------
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "5000"))

# --------------------------------------------------------------------------
# Paths and Directories
# --------------------------------------------------------------------------

RESOURCE_JSON_PATH = os.path.join(BASE_DIR,root_file_relative, "resource.json")
SWITCH_CONFIG_PATH = os.path.join(BASE_DIR,root_file_relative, "switch_config.json")


ACTIVE_USERS_PATH  = os.path.join(BASE_DIR, "active_users.json")
NODE_CONFIG_PATH  = os.path.join(BASE_DIR, "nfs_node_configs.json")

# If you have a separate CSV in a different location, you can keep it as-is:
RESSOURCE_CSV_PATH = os.getenv(
    "RESSOURCE_CSV_PATH",
    "/home/fs-5gmmtclab/Workspace/list_devices.csv"
)

###
## switch config
###

SWITCH_PASSWORD = os.getenv("SWITCH_PASSWORD","")
SWITCH_SECRET = os.getenv("SWITCH_SECRET","")
# --------------------------------------------------------------------------
# Logging Settings
# --------------------------------------------------------------------------


# Get the logs directory name from environment or default to "../logs"
LOGS_DIR = os.getenv("SYSTEM_MANAGER_LOG_DIR", "../logs")

# Build an absolute path to the logs directory, based on BASE_DIR
LOGS_DIR_PATH = os.path.abspath(os.path.join(BASE_DIR, LOGS_DIR))

# Ensure the logs directory actually exists; if not, create it (optional).
os.makedirs(LOGS_DIR_PATH, exist_ok=True)

SYSTEM_MANAGER_LOG_FILE  = os.getenv("SYSTEM_MANAGER_LOG_FILE", "system_manager.log")
SYSTEM_MANAGER_LOG_FILE  = os.path.join(LOGS_DIR_PATH, SYSTEM_MANAGER_LOG_FILE )
# Logging level handling
SYSTEM_MANAGER_LOG_LEVEL = os.getenv("SYSTEM_MANAGER_LOG_LEVEL", "INFO").upper()

LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
SYSTEM_MANAGER_LOG_LEVEL= LOG_LEVEL_MAP.get(SYSTEM_MANAGER_LOG_LEVEL, logging.INFO)


# Logging format
LOGGING_FORMAT = os.getenv("LOGGING_FORMAT", "%(asctime)s - %(levelname)s - %(message)s")
