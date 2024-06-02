import subprocess
from network_interface import NetworkInterface
import json
from macvlan import MacVlan





def create_user_vm(ubuntu_version, vm_name, root_size):
    # Construct the command using an f-string
    command = f"lxc launch ubuntu:{ubuntu_version} {vm_name} --vm --device root,size={root_size}"


    try:
        # Execute the command
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        # Print the output if successful
        print("STDOUT:", result.stdout)
    except subprocess.CalledProcessError as e:
        # Print the error details
        print("Command failed with return code:", e.returncode)
        print("Command output:", e.output)
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)




def create_macvlan_for_vm(macvlan_manager, macvlan_name):

    if macvlan_manager.macvlan_exists(macvlan_name) == False:
        macvlan_manager.create_macvlan(macvlan_name)
        macvlan_manager.set_ip_addr(macvlan_ip_addr, macvlan_name)

    else:
        print("Macvlan for user exists")


def delete_macvlan_for_vm(macvlan_manager, macvlan_name):
    
    if macvlan_manager.macvlan_exists(macvlan_name) == True:
        macvlan_manager.delete_macvlan(macvlan_name)
    else:
        print(f"{macvlan_name} does not exist")


def attach_macvlan_to_vm(vm_name, macvlan_name):
    
    command = f"lxc config device add {vm_name} eth1 nic nictype=macvlan parent={macvlan_name}"
    
    try:
        # Execute the command
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        # Print the output if successful
        print("STDOUT:", result.stdout)
    except subprocess.CalledProcessError as e:
        # Print the error details
        print("Command failed with return code:", e.returncode)
        print("Command output:", e.output)
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)

    





# Define the parameters
ubuntu_version = "24.04"
vm_name = "testvm"
root_size = "4GiB"



user_info = {
        "user_name": "testvm",
        "user_network_id": 75,
        "user_subnet": "192.168.75.0/24",
        "nfs_ip_addr": "192.168.75.1/24",
        "macvlan_interface": "macvlan_testvm",
        "macvlan_ip_addr": "192.168.75.2/24"
    }


print(user_info)


# create vm for user

#create_user_vm(ubuntu_version, vm_name, root_size)


# Extracting the information
macvlan_name = user_info["macvlan_interface"]
user_name = user_info["user_name"]
macvlan_ip_addr = user_info["macvlan_ip_addr"]

# interface name on which macvlan is to be created
interface_name = "enp2s0"

macvlan_manager = MacVlan(interface_name)

print(macvlan_ip_addr)

#create_macvlan_for_vm(macvlan_manager, macvlan_name)

# delete_macvlan_for_vm(macvlan_manager, macvlan_name)
attach_macvlan_to_vm(vm_name, macvlan_name)