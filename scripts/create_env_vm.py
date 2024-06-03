import subprocess
from network_interface import NetworkInterface
import json
from macvlan import MacVlan



class VmManager():
    
    
    def create_user_vm(self, ubuntu_version, vm_name, root_size):
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



    def is_vm_running(self, vm_name):
        # Command to check if the instance is running
        list_command = ["lxc", "list", vm_name, "--format", "json"]
        
        try:
            result = subprocess.run(list_command, capture_output=True, text=True, check=True)
            instances = json.loads(result.stdout)
            
            if instances and instances[0]["name"] == vm_name and instances[0]["status"] == "Running":
                return True
            else:
                return False
        except subprocess.CalledProcessError as e:
            print("Failed to execute command:", e)
            print("STDOUT:\n", e.stdout)
            print("STDERR:\n", e.stderr)
            return False

    def delete_vm(self, vm_name):
        if self.is_vm_running(vm_name):
            delete_command = ["lxc", "delete", vm_name, "--force"]
            try:
                result = subprocess.run(delete_command, capture_output=True, text=True, check=True)
                print(f"VM {vm_name} has been deleted.")
            except subprocess.CalledProcessError as e:
                print("Failed to delete VM:", e)
                print("STDOUT:\n", e.stdout)
                print("STDERR:\n", e.stderr)
        else:
            print(f"VM {vm_name} is not running or does not exist.")



    def create_macvlan_for_vm(self, macvlan_manager, macvlan_name):

        if macvlan_manager.macvlan_exists(macvlan_name) == False:
            macvlan_manager.create_macvlan(macvlan_name)
            macvlan_manager.set_ip_addr(macvlan_ip_addr, macvlan_name)

        else:
            print("Macvlan for user exists")


    def delete_macvlan_for_vm(self, macvlan_manager, macvlan_name):
        
        if macvlan_manager.macvlan_exists(macvlan_name) == True:
            macvlan_manager.delete_macvlan(macvlan_name)
        else:
            print(f"{macvlan_name} does not exist")


    def interface_check(self, vm_name, interface_name):
        check_interface_command = ["lxc", "exec", vm_name, "--", "ip", "-c", "a"]

        try:
            # Run the command to list network interfaces
            result = subprocess.run(check_interface_command,
                                    capture_output=True, 
                                    text=True, 
                                    check=True)
            #print("Command output:\n", result.stdout)

            # Check if the interface name is in the output
            if interface_name in result.stdout:
                print(f"Interface {interface_name} is present.")
                return True
            else:
                print(f"Interface {interface_name} is not present.")
                return False
        
        
        except subprocess.CalledProcessError as e:
            print("Failed to execute command:", e)
            print("STDOUT:\n", e.stdout)
            print("STDERR:\n", e.stderr)
            return False


    def attach_macvlan_to_vm(self, vm_name, macvlan_name):    
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


    def set_nfs_ip_addr(self, vm_name, nfs_ip_addr):
        interface_name = "enp6s0"
        
        if self.interface_check(vm_name, interface_name):
            # Command to check current IP addresses
            command_check_ip = ["lxc", "exec", vm_name, "--", "ip", "addr", "show", interface_name]
            
            try:
                result = subprocess.run(command_check_ip, capture_output=True, text=True, check=True)
                # Check if the desired IP address is already allocated
                if nfs_ip_addr in result.stdout:
                    print(f"IP address {nfs_ip_addr} is already allocated to {interface_name}. Skipping IP addition.")
                    return
            except subprocess.CalledProcessError as e:
                print("Failed to execute command:", e)
                print("STDOUT:\n", e.stdout)
                print("STDERR:\n", e.stderr)
                return
            
            # Add the IP address if not already allocated
            command_add_ip = ["lxc", "exec", vm_name, "--", "ip", "addr", "add", nfs_ip_addr, "dev", interface_name]
            try:
                result = subprocess.run(command_add_ip, capture_output=True, text=True, check=True)
                print(f"IP address {nfs_ip_addr} added to {interface_name}.")
            except subprocess.CalledProcessError as e:
                print("Failed to execute command:", e)
                print("STDOUT:\n", e.stdout)
                print("STDERR:\n", e.stderr)
                return
            
            # Set the interface up
            command_set_interface_up = ["lxc", "exec", vm_name, "--", "ip", "link", "set", "dev", interface_name, "up"]
            try:
                result = subprocess.run(command_set_interface_up, capture_output=True, text=True, check=True)
                print(f"Interface {interface_name} set up.")
            except subprocess.CalledProcessError as e:
                print("Failed to execute command:", e)
                print("STDOUT:\n", e.stdout)
                print("STDERR:\n", e.stderr)



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


# Extracting the information
macvlan_name = user_info["macvlan_interface"]
user_name = user_info["user_name"]
macvlan_ip_addr = user_info["macvlan_ip_addr"]
nfs_ip_addr = user_info["nfs_ip_addr"]

# interface name on which macvlan is to be created
interface_name = "enp2s0"


macvlan_manager = MacVlan(interface_name)
vm_manager = VmManager()

# #---------------
# # create vm for user
# vm_manager.create_user_vm(ubuntu_version, vm_name, root_size)

# # macvlan

# print(macvlan_ip_addr)

# vm_manager.create_macvlan_for_vm(macvlan_manager, macvlan_name)

# vm_manager.attach_macvlan_to_vm(vm_name, macvlan_name)

# res = vm_manager.interface_check(vm_name, "enp6s0")
# print(res)

# vm_manager.set_nfs_ip_addr(vm_name, nfs_ip_addr)
# #----------------

vm_manager.delete_vm(vm_name)
vm_manager.delete_macvlan_for_vm(macvlan_manager, macvlan_name)



