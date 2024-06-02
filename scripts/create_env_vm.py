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








# Define the parameters
ubuntu_version = "24.04"
vm_name = "testvm"
root_size = "4GiB"



user_info = {
        "user_name": "cedric",
        "user_network_id": 75,
        "user_subnet": "192.168.75.0/24",
        "nfs_ip_addr": "192.168.75.1/24",
        "macvlan_interface": "macvlan_cedric",
        "macvlan_ip_addr": "192.168.75.2/24"
    }

#create_user_vm(ubuntu_version, vm_name, root_size)
print(user_info)

interface_name = "enp2s0"
macvlan_ip = user_info["macvlan_ip_addr"]


print(macvlan_ip)
macvlan_manager = MacVlan(interface_name)
print(macvlan_manager.macvlan_exists("macrootfs"))

#creator.set_ip_addr(ip_addr, macvlan)