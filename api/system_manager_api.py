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

#get_resource_list()
power_all_off()

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)


