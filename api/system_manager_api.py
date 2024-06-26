from fastapi import FastAPI
from subprocess import run, CalledProcessError
import os
import sys
import json
import time

# Get the absolute path of the parent directory
script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts'))
sys.path.append(script_path)
# Now import the function from the script
from create_env import launch_env
from destroy_env import destroy_user_env
from user_env import UserEnv
from jetson_ctl import Jetson
from ip_addr_manager import IpAddr
from create_env_vm import VmManager
from macvlan import MacVlan


# Switch imports
# Get the absolute path of the parent directory
switch_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../switch'))
sys.path.append(switch_path)
from switch_manager import SwitchManager
from poe_manager import PoeManager


# Specify the path to your JSON file
switch_config = "switch/switch_config.json"

# Open and load the JSON file
with open(switch_config, 'r') as file:
    switch_config = json.load(file)


## for containers
def create_env(config: UserEnv):
    launch_env(config)
        
## For containers
def destroy_env(config: UserEnv):
    destroy_user_env(config)


def get_resource_list():
    # Get the absolute path to the resource.json file
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, '../data')
    json_path = os.path.join(data_dir, 'resource.json')
    # Read the JSON file
    with open(json_path, 'r') as file:
        data = json.load(file)
        
    return data



def testbed_reset():   
    device = switch_config
    switch = SwitchManager(device_type = device['device_type'],
                                ip = device['ip'],
                                port = device['port'],
                                password = device['password'])
    power = PoeManager(switch)
    switch_interfaces = power.get_switch_interfaces()
    print(switch_interfaces)
    power.turn_all_off()

    
def turn_on_all_nodes():
    device = switch_config
    switch = SwitchManager(device_type = device['device_type'],
                                ip = device['ip'],
                                port = device['port'],
                                password = device['password'])

    power = PoeManager(switch)
    switch_interfaces = power.get_switch_interfaces()
    print(switch_interfaces)
    power.turn_all_on()




def allocate_active_users(user_name, user_network_id):

    if user_network_id > 254 or user_network_id < 3:
        print("Error: choose user_network_id between 3 and 253")

        return 
    # Get the absolute path to the active users JSON file
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, '../data')
    active_users_path = os.path.join(data_dir, 'active_users.json')

    # Read existing user data from the active users JSON file
    existing_users = []
    try:
        with open(active_users_path, 'r') as file:
            existing_users = json.load(file)
    except FileNotFoundError:
        pass  # File doesn't exist yet, which is fine, we'll create it later

    # Check if the user already exists
    user_name_exists = any(user["user_name"] == user_name for user in existing_users)
    user_network_id_exists = any(user["user_network_id"] == user_network_id for user in existing_users)

    if user_network_id_exists:
        print(f"Error: User number {user_network_id} is already allocated to another user.")
        return
    elif user_name_exists:
        print(f"Error: User name {user_name} is already allocated to another user.")
        return
    else:
        # If user doesn't exist, allocate IP addresses and add the user
        ip_addr = IpAddr()

        user_subnet = ip_addr.user_subnet(user_network_id)
        nfs_ip_addr = ip_addr.nfs_interface_ip(user_network_id)
        macvlan_ip_addr = ip_addr.macvlan_interface_ip(user_network_id)

        # macvlan name
        user_macvlan = f"macvlan_{user_name}"

        
        # Create user data
        new_user = {
            "user_name": user_name,
            "user_network_id": user_network_id,
            "user_subnet": user_subnet,
            "nfs_ip_addr": nfs_ip_addr,
            "macvlan_interface": user_macvlan,
            "macvlan_ip_addr": macvlan_ip_addr
        }

        # Append user data to the existing users list
        existing_users.append(new_user)

        # Write the updated user data back to the active users JSON file
        with open(active_users_path, 'w') as file:
            json.dump(existing_users, file, indent=4)

        print(f"User allocation {user_name} with the user number {user_network_id} updated successfully.")



def clear_active_users():
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, '../data')
    active_users_path = os.path.join(data_dir, 'active_users.json')
    
    with open(active_users_path, 'r') as file:
        existing_users = json.load(file)
        print(existing_users)
        existing_users.clear()

    # Open the file in write mode and write the cleared list to it
    with open(active_users_path, 'w') as file:
        json.dump(existing_users, file, indent=4)

    if existing_users == []:
        print("Active Users Cleared")


def get_user_info(user_name, user_network_id):
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, '../data')
    active_users_path = os.path.join(data_dir, 'active_users.json')
    
    with open(active_users_path, 'r') as file:
        active_users = json.load(file)

    # Filter the list based on user_name and user_network_id
    filtered_users = [user for user in active_users if user['user_name'] == user_name and user['user_network_id'] == user_network_id][0]
    # Convert the filtered list to a JSON object
    filtered_json = json.dumps(filtered_users)
    
    return filtered_json




## For VM
def destroy_user_env_vm(vm_name, macvlan_name):
    interface_name = "enp2s0"
    macvlan_manager = MacVlan(interface_name)
    vm_manager = VmManager()
    vm_manager.delete_vm(vm_name)
    vm_manager.delete_macvlan_for_vm(macvlan_manager, macvlan_name)


def check_args_type_create_user_env_vm(ubuntu_version, vm_name, root_size, user_info):
    # Check types of the arguments
    if not isinstance(ubuntu_version, str):
        raise TypeError(f"Expected 'ubuntu_version' to be a string, but got {type(ubuntu_version).__name__}")
    
    if not isinstance(vm_name, str):
        raise TypeError(f"Expected 'vm_name' to be a string, but got {type(vm_name).__name__}")
    
    if not isinstance(root_size, str):
        raise TypeError(f"Expected 'root_size' to be a string, but got {type(root_size).__name__}")
    
    if not isinstance(user_info, dict):
        raise TypeError(f"Expected 'user_info' to be a JSON string, but got {type(user_info).__name__}")
    
    

## For VM
def create_user_env_vm(ubuntu_version, vm_name, root_size, user_info):
    
    check_args_type_create_user_env_vm(ubuntu_version, vm_name, root_size, user_info)

    # Extracting the information
    macvlan_name = user_info["macvlan_interface"]
    user_name = user_info["user_name"]
    macvlan_ip_addr = user_info["macvlan_ip_addr"]
    nfs_ip_addr = user_info["nfs_ip_addr"]

    # interface name on which macvlan is to be created
    interface_name = "enp2s0"
    macvlan_manager = MacVlan(interface_name)
    vm_manager = VmManager()
    
    vm_manager.create_user_vm(ubuntu_version, vm_name, root_size)
    time.sleep(20)
    print(macvlan_ip_addr)

    vm_manager.create_macvlan_for_vm(macvlan_manager, macvlan_name)

    vm_manager.attach_macvlan_to_vm(vm_name, macvlan_name)

    res = vm_manager.interface_check(vm_name, "enp6s0")
    print(res)
    vm_manager.set_nfs_ip_addr(vm_name, nfs_ip_addr)


# TO IMPLEMENT
def flash_jetson(usb_instance):
    pass





print(get_user_info('cedric', 97))
# ----------------------
# Creating user env

# Define the parameters
# ubuntu_version = "24.04"
# vm_name = "testvm"
# root_size = "4GiB"
# user_info = {
#         "user_name": "testvm",
#         "user_network_id": 75,
#         "user_subnet": "192.168.75.0/24",
#         "nfs_ip_addr": "192.168.75.1/24",
#         "macvlan_interface": "macvlan_testvm",
#         "macvlan_ip_addr": "192.168.75.2/24"
#     }
# create_user_env_vm(ubuntu_version, vm_name, root_size, user_info)

# --------------------------
#
# --------------
# Destroying user env

# vm_name = "testvm"
# macvlan_interface = "macvlan_testvm"
# destroy_user_env_vm(vm_name, macvlan_interface)
# ---------------


# ------------------
# allocating users in the testbed

#allocate_active_users("cedric", 75)
#allocate_active_users("cedric", 76)
# ----------------------------
