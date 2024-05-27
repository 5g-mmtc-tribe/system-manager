from fastapi import FastAPI
from subprocess import run, CalledProcessError
import os
import sys
import json

# Get the absolute path of the parent directory
script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts'))
sys.path.append(script_path)
# Now import the function from the script
from create_env import launch_env
from destroy_env import destroy_user_env
from user_env import UserEnv
from jetson_ctl import Jetson
from ip_addr_manager import IpAddr


# Switch imports
# Get the absolute path of the parent directory
switch_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../switch'))
sys.path.append(switch_path)
from switch_manager import SwitchManager

app = FastAPI()

def create_env(config: UserEnv):
    launch_env(config)
        

def destroy_env(config: UserEnv):
    destroy_user_env(config)


def get_active_jetsons_list():
    jetson = Jetson()
    print(jetson.list_devices())



def get_resource_list():
    # Get the absolute path to the resource.json file
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, '../data')
    json_path = os.path.join(data_dir, 'resource.json')



    # Read the JSON file
    with open(json_path, 'r') as file:
        data = json.load(file)
        
    return data


def power_all_off():
    device = {
            'device_type': 'cisco_ios_telnet',
            'ip': '192.168.0.30',
            'port':23,
            'password': 'tribe',
            }
    switch = SwitchManager(device_type = device['device_type'],
                            ip = device['ip'],
                            port = device['port'],
                            password = device['password'])



    jetson_complete_list = get_resource_list()
    for devices in jetson_complete_list:
        interface = devices['switch_interface']
        print(interface)

        switch.poe_off(interface)

def power_all_on():
    device = {
            'device_type': 'cisco_ios_telnet',
            'ip': '192.168.0.30',
            'port':23,
            'password': 'tribe',
            }
    switch = SwitchManager(device_type = device['device_type'],
                            ip = device['ip'],
                            port = device['port'],
                            password = device['password'])



    jetson_complete_list = get_resource_list()
    for devices in jetson_complete_list:
        interface = devices['switch_interface']
        print(interface)

        switch.poe_on(interface)

    


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
    user_network_id_exists = any(user["user_network_id"] == user_network_id for user in existing_users)

    if user_network_id_exists:
        print(f"Error: User number {user_network_id} is already allocated to another user.")
        return
    else:
        # If user doesn't exist, allocate IP addresses and add the user
        ip_addr = IpAddr()
        nfs_ip_addr = ip_addr.nfs_interface_ip(user_network_id)
        macvlan_ip_addr = ip_addr.macvlan_interface_ip(user_network_id)

        # macvlan name


        user_macvlan = f"macvlan_{user_name}"
        # Create user data
        new_user = {
            "user_name": user_name,
            "user_network_id": user_network_id,
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



def flash_jetson(usb_instance):
    pass


allocate_active_users("cedric", 75)
allocate_active_users("user_test", 76)


#clear_active_users()

#get_resource_list()
#power_all_off()

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)


