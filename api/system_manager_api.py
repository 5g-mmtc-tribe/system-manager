from fastapi import FastAPI, HTTPException
import os
import sys
import json
import time
import pandas as pd
import logging
from subprocess import run, CalledProcessError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the scripts directory to sys.path
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts'))
sys.path.append(SCRIPT_DIR)

# Import functions from scripts
from create_env import launch_env
from destroy_env import destroy_user_env
from user_env import UserEnv
from jetson_ctl import Jetson
from ip_addr_manager import IpAddr
from create_env_vm import VmManager
from macvlan import MacVlan
from container_create import Container

# Add the switch directory to sys.path
SWITCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../switch'))
sys.path.append(SWITCH_DIR)
from switch_manager import SwitchManager
from poe_manager import PoeManager

# Global configuration paths
SWITCH_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../switch/switch_config.json'))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
ACTIVE_USERS_PATH = os.path.join(DATA_DIR, 'active_users.json')
RESOURCE_JSON_PATH = os.path.join(DATA_DIR, 'resource.json')

def load_switch_config():
    """
    Load and return the switch configuration from the JSON file.
    """
    try:
        with open(SWITCH_CONFIG_PATH, 'r') as file:
            config = json.load(file)
        return config
    except Exception as e:
        logging.error("Failed to load switch config: %s", e)
        raise

SWITCH_CONFIG = load_switch_config()

def get_switch_and_poe():
    """
    Helper function to initialize and return both the SwitchManager and PoeManager.
    """
    config = SWITCH_CONFIG
    switch = SwitchManager(
        device_type=config.get('device_type'),
        ip=config.get('ip'),
        port=config.get('port'),
        password=config.get('password')
    )
    poe = PoeManager(switch)
    return switch, poe

# Create FastAPI instance (endpoints can be added later)
app = FastAPI()

# ---------------------------
# Environment Management
# ---------------------------

def create_env(config: UserEnv):
    """
    Launch the environment for a user.
    """
    launch_env(config)

def destroy_env(config: UserEnv):
    """
    Destroy the user environment.
    """
    destroy_user_env(config)

def get_resource_list():
    """
    Load and return the resource list from resource.json.
    """
    try:
        with open(RESOURCE_JSON_PATH, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        logging.error("Error reading resource list: %s", e)
        raise

# ---------------------------
# Switch Operations
# ---------------------------

def testbed_reset():
    """
    Reset the testbed by turning off all nodes.
    """
    logging.info("Resetting testbed: turning off all nodes.")
    _, poe = get_switch_and_poe()
    poe.turn_all_off()

def turn_on_all_nodes():
    """
    Turn on all nodes in the testbed.
    """
    logging.info("Turning on all nodes.")
    _, poe = get_switch_and_poe()
    poe.turn_all_on()

def turn_on_node(interface: str):
    """
    Turn on a specific node by its interface.
    """
    _, poe = get_switch_and_poe()
    poe.turn_on(interface)
    logging.info("Interface '%s' is up", interface)

def turn_off_node(interface: str):
    """
    Turn off a specific node by its interface.
    """
    _, poe = get_switch_and_poe()
    poe.turn_off(interface)
    logging.info("Interface '%s' is down", interface)

def attach_vlan_device_interface(interface: str, vlan_id: int):
    """
    Attach a VLAN to a specific device interface.
    """
    switch, _ = get_switch_and_poe()
    switch.vlan_access(interface, vlan_id)
    time.sleep(10)  # Consider making this delay configurable or async.
    logging.info("Interface '%s' set to VLAN %s", interface, vlan_id)

def get_switch_interface(device_name: str) -> str:
    """
    Return the switch interface associated with a given device name.
    
    Raises:
        ValueError: If the device name is not found.
    """
    df = pd.DataFrame(get_resource_list())
    result = df[df['name'] == device_name]
    if not result.empty:
        return result.iloc[0]['switch_interface']
    else:
        error_msg = f"Device name '{device_name}' not found"
        logging.error(error_msg)
        raise ValueError(error_msg)

# ---------------------------
# Active Users Management
# ---------------------------

def allocate_active_users(user_name: str, user_network_id: int):
    """
    Allocate a new user by adding them to the active users JSON.
    """
    if user_network_id > 254 or user_network_id < 3:
        logging.error("Choose user_network_id between 3 and 253")
        return

    try:
        with open(ACTIVE_USERS_PATH, 'r') as file:
            existing_users = json.load(file)
    except FileNotFoundError:
        existing_users = []

    if any(user["user_network_id"] == user_network_id for user in existing_users):
        logging.error("User number %s is already allocated.", user_network_id)
        return
    elif any(user["user_name"] == user_name for user in existing_users):
        logging.error("User name %s is already allocated.", user_name)
        return
    else:
        ip_addr = IpAddr()
        user_subnet = ip_addr.user_subnet(user_network_id)
        nfs_ip_addr = ip_addr.nfs_interface_ip(user_network_id)
        user_macvlan = f"macvlan_{user_name}"
        new_user = {
            "user_name": user_name,
            "user_network_id": user_network_id,
            "user_subnet": user_subnet,
            "nfs_ip_addr": nfs_ip_addr,
            "macvlan_interface": user_macvlan,
        }
        existing_users.append(new_user)
        with open(ACTIVE_USERS_PATH, 'w') as file:
            json.dump(existing_users, file, indent=4)
        logging.info("User %s allocated with network ID %s", user_name, user_network_id)

def clear_active_users():
    """
    Clear all active users from the active users JSON file.
    """
    try:
        with open(ACTIVE_USERS_PATH, 'r') as file:
            existing_users = json.load(file)
        existing_users.clear()
        with open(ACTIVE_USERS_PATH, 'w') as file:
            json.dump(existing_users, file, indent=4)
        logging.info("Active Users Cleared")
    except Exception as e:
        logging.error("Failed to clear active users: %s", e)

def get_user_info(user_name: str, user_network_id: int):
    """
    Retrieve and return user information as a JSON string.
    """
    try:
        with open(ACTIVE_USERS_PATH, 'r') as file:
            active_users = json.load(file)
        filtered_users = [
            user for user in active_users 
            if user['user_name'] == user_name and user['user_network_id'] == user_network_id
        ]
        if not filtered_users:
            error_msg = f"No user info found for {user_name} with network ID {user_network_id}"
            logging.error(error_msg)
            raise ValueError(error_msg)
        return json.dumps(filtered_users[0])
    except Exception as e:
        logging.error("Error getting user info: %s", e)
        raise

# ---------------------------
# VM Management
# ---------------------------

def destroy_user_env_vm(vm_name: str, macvlan_name: str):
    """
    Destroy a VM environment and remove the associated macvlan interface.
    """
    interface_name = "eno1"  # Update as needed.
    macvlan_manager = MacVlan(interface_name)
    vm_manager = VmManager()
    vm_manager.delete_vm(vm_name)
    vm_manager.delete_macvlan_for_vm(macvlan_manager, macvlan_name)

def check_args_type_create_user_env_vm(ubuntu_version: str, vm_name: str, root_size: str, user_info: dict):
    """
    Validate argument types for creating a user VM environment.
    """
    if not isinstance(ubuntu_version, str):
        raise TypeError(f"Expected 'ubuntu_version' to be a string, got {type(ubuntu_version).__name__}")
    if not isinstance(vm_name, str):
        raise TypeError(f"Expected 'vm_name' to be a string, got {type(vm_name).__name__}")
    if not isinstance(root_size, str):
        raise TypeError(f"Expected 'root_size' to be a string, got {type(root_size).__name__}")
    if not isinstance(user_info, dict):
        raise TypeError(f"Expected 'user_info' to be a dict, got {type(user_info).__name__}")

def update_ssh(user_name: str):
    """
    Update SSH keys for the given user.
    """
    vm_manager = VmManager()
    vm_manager.add_ssh_key_to_lxd(user_name, user_name)

def create_user_env_vm(ubuntu_version: str, vm_name: str, root_size: str, user_info: dict, nodes):
    """
    Create a VM environment for the user.
    
    Returns:
        A dict with the VM IP address and status.
    """
    check_args_type_create_user_env_vm(ubuntu_version, vm_name, root_size, user_info)
    macvlan_name = user_info["macvlan_interface"]
    user_name = user_info["user_name"]
    nfs_ip_addr = user_info["nfs_ip_addr"]
    user_network_id = user_info["user_network_id"]

    interface_name = "eno1"  # Update as needed.
    vm_manager = VmManager()
    existed = vm_manager.create_user_vm(ubuntu_version, vm_name, root_size)
    
    if existed["created"]:
        time.sleep(20)
        vm_manager.create_macvlan_for_vm(user_name, user_network_id, SWITCH_CONFIG, interface_name, macvlan_name)
        res = vm_manager.interface_check(vm_name, "enp6s0")
        time.sleep(10)
        logging.info("Interface check result: %s", res)
        vm_manager.set_nfs_ip_addr(vm_name, nfs_ip_addr)
        vm_manager.install_library_for_flashing_jetson(vm_name, nfs_ip_addr)
        time.sleep(2)
        vm_manager.add_ssh_key_to_lxd(user_name, user_name)
        vm_manager.setup_nfs_jetson(user_name, nodes)
        vm_manager.configure_nbd_on_lxc_vm(vm_name, nfs_ip_addr.split('/')[0])
        return {"vm_ip_address": "10.0.0.0", "status": "User Env Created"}
    else:
        vm_manager.start_vm(vm_name)
        vm_manager.add_ssh_key_to_lxd(user_name, user_name)
        vm_manager.setup_nfs_jetson(user_name, nodes)
        return {"vm_ip_address": "10.0.0.0", "status": "User Env Created"}

def stop_user_vm(vm_name: str):
    """
    Stop the specified VM.
    """
    vm_manager = VmManager()
    vm_manager.stop_vm(vm_name)

def flash_jetson(nfs_ip_address: str, nfspath: str, usb_instance: str, switch_interface: str ,model:str ,nvidia_id:str):
    """
    Flash a Jetson device using the provided parameters.
    
    Returns:
        The result of the flash operation or an error message.
    """
    try:
        turn_off_node(switch_interface)
        turn_on_node(switch_interface)
        logging.info("Flashing Jetson with NFS IP: %s, NFS Path: %s, USB Instance: %s", nfs_ip_address, nfspath, usb_instance ,model ,nvidia_id)
        jetson = Jetson()
        result = jetson.flash_jetson(nfs_ip_address, nfspath, usb_instance,model ,nvidia_id)
        return result
    except Exception as e:
        logging.error("Error flashing Jetson: %s", e)
        return str(e)

# ---------------------------
# Module Test Section
# ---------------------------
if __name__ == "__main__":
    # Sample test for create_user_env_vm (uncomment as needed)
    ubuntu_version = "24.04"
    vm_name = "debbah"
    root_size = "40GiB"
    user_info = {
        "user_name": "debbah",
        "user_network_id": 226,
        "user_subnet": "192.168.0.226/24",
        "nfs_ip_addr": "192.168.0.227/24",
        "macvlan_interface": "macvlan_debbah",
        "macvlan_ip_addr": "192.168.0.228/24"
    }
    # Example call:
    # create_user_env_vm(ubuntu_version, vm_name, root_size, user_info, nodes=None)
    #testbed_reset()