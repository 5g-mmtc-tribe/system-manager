import subprocess
from fastapi import FastAPI, HTTPException, Path
import os
import sys
import json
import time
import pandas as pd
import logging
from subprocess import run, CalledProcessError

# Configure logging
# Setup module-level logger
logger = logging.getLogger(__name__)


# Import functions from scripts
from config import DRIVER_RPI4, DRIVER_RPI4_PATH, NODE_CONFIG_PATH, ROOT_FS_RPI4, SWITCH_PASSWORD, SWITCH_SECRET
from scripts.create_env import launch_env
from scripts.destroy_env import destroy_user_env
from scripts.user_env import UserEnv
from scripts.jetson_ctl import Jetson
from scripts.ip_addr_manager import IpAddr
from scripts.create_env_vm import VmManager
from scripts.macvlan import MacVlan
from scripts.container_create import Container
# switch import 
from switch.switch_manager import SwitchManager
from switch.poe_manager import PoeManager

# Global configuration paths
from config.config import SWITCH_CONFIG_PATH ,ACTIVE_USERS_PATH ,RESOURCE_JSON_PATH ,RESSOURCE_CSV_PATH ,VPN_NAME ,HOST_INTERFACE, VM_INTERFACE
from config.constants import ROOT_FS_3274 ,ROOT_FS_3541 ,TOOLS_SCRIPT_PATH ,USER_SCRIPT_PATH_3271 ,USER_SCRIPT_PATH_3274 ,DRIVER_3274 ,DRIVER_3541 ,DRIVER_3274_PATH, DRIVER_3541_PATH


# old imports
#SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts'))
#sys.path.append(SCRIPT_DIR)
# Add the switch directory to sys.path
#SWITCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../switch'))
#sys.path.append(SWITCH_DIR)




def load_switch_config():
    """
    Load and return the switch configuration from the JSON file.
    """
    try:
        with open(SWITCH_CONFIG_PATH, 'r') as file:
            config = json.load(file)

        # config_data has fields like "password" and "secret_env"
        password_env_key = config.pop("password", None)
        secret_env_key = config.pop("secret", None)

        if password_env_key:
            config["password"] = SWITCH_PASSWORD
        if secret_env_key:
            config["secret"] =SWITCH_SECRET

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
        password=config.get('password'),
        #username= config.get('username')
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

def update_ressource_from_platforme(list_ressource_csv, list_ressource_json):
    """update ressource from the platforme csv """
    result = subprocess.run(
        ["python3", TOOLS_SCRIPT_PATH+"/csv_to_json.py", list_ressource_csv , list_ressource_json],
        capture_output=True,
        text=True
    )
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    return result.returncode

def get_resource_list():
    """
    Load and return the resource list from resource.json.
    """
    try:
        # update
        #update_ressource_from_platforme(RESSOURCE_CSV_PATH,RESOURCE_JSON_PATH)
        with open(RESOURCE_JSON_PATH, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        logging.error("Error reading resource list: %s", e)
        raise
def update_resource(name):
    """
    Load and return the update resource  from resource.json.
    """
    try:

        with open(RESOURCE_JSON_PATH, 'r') as file:
            data = json.load(file)
            for ressource in data :
                if name in ressource["name"]: 
                    return ressource
 
       
    except Exception as e:
        logging.error("Error reading resource list: %s", e)
        raise

def load_node_configs(path: Path) -> dict[str, dict]:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error("Impossible de charger la config NFS (%s): %s", path, e)
        return {}

    # Helper: identify Jetson nodes only
node_nfs_configs = load_node_configs(NODE_CONFIG_PATH)

def configure_and_setup_nfs_nodes(
    vm_manager,
    user_name: str,
    vm_name: str,
    nfs_ip_addr: str,
    nodes: list[str],
    config_path: Path = NODE_CONFIG_PATH
) -> None:
    """
    For each node in the list:
      1. Determine whether it's a Jetson (pattern starts with 'j')
         or a Raspberry Pi (pattern starts with 'rpi').
      2. Extract the 'nfsroot-xxx' directory name from the full rootfs path.
      3. First configure NFS exports/mounts via configure_nfs_*.
      4. Then set up the NFS overlay via setup_nfs_*.
    """
    configs = load_node_configs(config_path)
    if not configs:
        return

    for node in nodes:
        # 1) Find the first pattern key that appears in the node name
        matched = next((pattern for pattern in configs if pattern in node), None)
        if not matched:
            logging.warning("No NFS config found for node '%s'; skipping.", node)
            continue

        cfg = configs[matched]
        logging.info("Node '%s' matched pattern '%s': %s", node, matched, cfg)

        # 2) Extract the third segment of the rootfs path (e.g. "nfsroot-3541")
        try:
            rootfs_dir = cfg["rootfs"].split("/")[2]
        except (KeyError, IndexError):
            logging.error(
                "Unable to extract rootfs directory from '%s' for node '%s'",
                cfg.get("rootfs"), node
            )
            continue

        # 3 & 4) Configure exports and then set up overlay
        if matched.startswith("rpi"):
            rpi_version = matched
            # Raspberry Pi flow
            vm_manager.configure_nfs_raspberry(
                vm_name,
                cfg["rootfs"],
                cfg["driver"],
                cfg["driver_path"]
            
            )
            """vm_manager.setup_nfs_rpi(
                user_name,
                rootfs_dir,
                [node],
            )"""
            vm_manager.setup_tftp_for_rpi_lxc(vm_name,rpi_version)
        elif matched.startswith("j"):
            # Jetson flow
            vm_manager.configure_nfs_jetson(
                vm_name,
                nfs_ip_addr,
                cfg["rootfs"],
                cfg["driver"],
                cfg.get("user_script_path"),
                cfg["driver_path"]
            )
            vm_manager.setup_nfs_jetson(
                user_name,
                rootfs_dir,
                [node]
            )
        else:
            logging.warning(
                "Pattern '%s' for node '%s' is not supported; skipping.",
                matched, node
            )
            continue

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
    interface_name = HOST_INTERFACE # Update as needed.
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

    interface_name = HOST_INTERFACE # Update as needed.
    vm_manager = VmManager()
    existed = vm_manager.create_user_vm(ubuntu_version, vm_name, root_size)
    jetson_nodes = [
    node for node in nodes
    if next((pat for pat in node_nfs_configs if pat in node and pat.startswith("j")), None)
    ]   
    if existed["created"]:
        time.sleep(20)
        vm_manager.create_macvlan_for_vm(user_name, user_network_id, SWITCH_CONFIG, interface_name, macvlan_name)
        res = vm_manager.interface_check(vm_name, VM_INTERFACE)
        time.sleep(10)
        logging.info("Interface check result: %s", res)
        vm_manager.set_nfs_ip_addr(vm_name, nfs_ip_addr)
        vm_manager.install_library(vm_name, nfs_ip_addr)

        
        # Configure and set up NFS for all nodes
        configure_and_setup_nfs_nodes(
            vm_manager,
            user_name,
            vm_name,
            nfs_ip_addr,
            nodes,
            config_path=NODE_CONFIG_PATH
        )

        vm_manager.create_dhcp_server(vm_name, nfs_ip_addr)
        vm_manager.configure_vm_nat(vm_name)
        
        time.sleep(2)
        vm_manager.add_ssh_key_to_lxd(user_name, user_name)

        if jetson_nodes:
            vm_manager.configure_nbd_on_lxc_vm(vm_name, nfs_ip_addr.split('/')[0],jetson_nodes)
        ## add vpn interface if the vlan 
        vm_manager.setup_vpn_vlan(VPN_NAME, user_network_id)
        return {"vm_ip_address": "10.0.0.0", "status": "User Env Created"}
    
    else:
        vm_manager.start_vm(vm_name)
        # Configure and set up NFS for all nodes
        configure_and_setup_nfs_nodes(
            vm_manager,
            user_name,
            vm_name,
            nfs_ip_addr,
            nodes,
            config_path=NODE_CONFIG_PATH
        )
        if jetson_nodes:
            vm_manager.configure_nbd_on_lxc_vm(vm_name, nfs_ip_addr.split('/')[0],jetson_nodes)
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
    #turn_off_node("GigabitEthernet1/0/25")
    #turn_on_node("GigabitEthernet1/0/26")
#update_ressource_from_platforme(RESSOURCE_CSV_PATH ,RESOURCE_JSON_PATH)
