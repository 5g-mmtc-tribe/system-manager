import subprocess
from network_interface import NetworkInterface
import json
import os ,sys
from macvlan import MacVlan
# Get the absolute path of the parent directory
script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts'))
sys.path.append(script_path)
from ip_addr_manager import IpAddr



class VmManager():
    # Get the absolute path to the resource.json file
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, '../data')
    bsp_path = os.path.join(data_dir, 'jetson_linux_r35.4.1_aarch64.tbz2')
    rootfs_path = os.path.join(data_dir, 'tegra_linux_sample-root-filesystem_r35.4.1_aarch64.tbz2')
    def start_vm(self, vm_name):
        # To flash the jetson, the usb must be inside the vm. here's a way to do it.
        command_librray_install=   ["lxc", "config","device","remove" ,vm_name,  "Nvidia"]
        print("command",command_librray_install)
        try:
            result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
            print("STDOUT:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Failed to execute command:", e)
            print("STDOUT:\n", e.stdout)
            print("STDERR:\n", e.stderr)
            return
        # To flash the jetson, the usb must be inside the vm. here's a way to do it.
        command_librray_install=   ["lxc", "config","device","add" ,vm_name,  "Nvidia" ,"usb", "vendorid=0955", "productid=7e19"]
        print("command",command_librray_install)
        try:
            result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
            print("STDOUT:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Failed to execute command:", e)
            print("STDOUT:\n", e.stdout)
            print("STDERR:\n", e.stderr)
            return
        command = ['lxc', 'start', vm_name]
        try:
            result =subprocess.run(command, check=True)
            print("STDOUT:", result.stdout)
        except subprocess.CalledProcessError as e:
            # Print the error details
            print("Command failed with return code:", e.returncode)
            print("Command output:", e.output)
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
        

    def stop_vm(self, vm_name):

        command = ['lxc', 'stop', vm_name, '--force']
        try:
            result =subprocess.run(command, check=True)
            print("STDOUT:", result.stdout)
        except subprocess.CalledProcessError as e:
            # Print the error details
            print("Command failed with return code:", e.returncode)
            print("Command output:", e.output)
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)

    
    def create_user_vm(self, ubuntu_version, vm_name, root_size):
        # Construct the command using an f-string
        command = f"lxc launch ubuntu:{ubuntu_version} {vm_name} --vm --device root,size={root_size}"
        print("the commande ",command)
        try:
            # Execute the command
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            # Print the output if successful
            print("STDOUT:", result.stdout)
            return({"created":True})
        except subprocess.CalledProcessError as e:
            # Print the error details
            print("Command failed with return code:", e.returncode)
            print("Command output:", e.output)
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            return({"created":False})



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
            print(command_check_ip)
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
            print(command_add_ip)
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
            print(command_set_interface_up)
            try:
                result = subprocess.run(command_set_interface_up, capture_output=True, text=True, check=True)
                print(f"Interface {interface_name} set up.")
            except subprocess.CalledProcessError as e:
                print("Failed to execute command:", e)
                print("STDOUT:\n", e.stdout)
                print("STDERR:\n", e.stderr)


    def install_library_for_flashing_jetson(_self ,vm_name ,nfs_ip_addres):
                ip_addr = IpAddr()
                jetson_ip=ip_addr.jetson_ip(nfs_ip_addres)
                
                #installing the bzip2 package
                
                command_librray_install = ["lxc", "exec", vm_name, "--", "sudo", "apt-get", "install", "bzip2"]
                print("command",command_librray_install)
                
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                #installing the qemu
                command_librray_install = ["lxc", "exec", vm_name, "--", "sudo", "add-apt-repository", "universe"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                #installing the Update 
                command_librray_install = ["lxc", "exec", vm_name, "--", "sudo","apt-get" ,"update"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                # copy the the jeston the rootfs and the bsp to the vm 
                command_librray_install = ["sudo","lxc", "file","push" ,VmManager.bsp_path ,vm_name+"/root/" ]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout) 
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                command_librray_install = ["sudo","lxc", "file","push" ,VmManager.rootfs_path ,vm_name+"/root/"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout) 
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                    #extracting the jeston the rootfs and the bsp. 
                command_librray_install = ["lxc", "exec", vm_name, "--", "sudo", "tar","-xf" ,"/root/jetson_linux_r35.4.1_aarch64.tbz2" ,"-C","/root"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout) 
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                command_librray_install = ["lxc", "exec", vm_name,  "--","tar", "xpf" ,"/root/tegra_linux_sample-root-filesystem_r35.4.1_aarch64.tbz2", "-C","/root/Linux_for_Tegra/rootfs"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout) 
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                # apply_binaries for jetson
                command_librray_install = ["lxc", "exec", vm_name, "--", "sudo", "apt-get", "install", "qemu-user-static"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                command_librray_install =["lxc", "exec", vm_name, "--",  "/root/Linux_for_Tegra/apply_binaries.sh"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                #installing the libraries for  flashing the jetson
                command_librray_install = ["lxc", "exec", vm_name, "--", "sudo",   "apt-get", "install", "-y" ,"lz4" ]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                
                command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "apt-get" ,"install" ,"libxml2-utils"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return

                # To flash the jetson, the usb must be inside the vm. here's a way to do it.
                command_librray_install=   ["lxc", "config","device","add" ,vm_name,  "Nvidia" ,"usb", "vendorid=0955", "productid=7e19"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return 
                
                ## Create default user (EULA Acceptance / User configuration)
                command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "./Linux_for_Tegra/tools/l4t_create_default_user.sh" ,'-u' ,vm_name,'-p',vm_name ,'-n',vm_name,'--accept-license']
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                
                # Create NFS folder to be used on the Jetson (on the VM)
                
                vmcommand =["lxc", "exec", vm_name, "--", "sudo"]
                command_librray_install=   vmcommand +["mkdir" ,"/root/nfsroot" ]
                
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                
               
                vmcommand =["lxc", "exec", vm_name, "--"]
                command_librray_install = vmcommand +["chown","-R" ,"nobody:nogroup", "/root/nfsroot"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                command_librray_install = vmcommand+["sudo" ,"chmod" ,"755", "/root/nfsroot"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return

                 
                vmcommand =["lxc", "exec", vm_name, "--"]
                # Rsync original "rootfs" to "nfsroot"
                command_librray_install=   vmcommand +["sudo","rsync" ,"-aAXv" ,"Linux_for_Tegra/rootfs/" ,"/root/nfsroot"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                
                # Setting up the NFS server inside the VM
                command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "apt" ,"install" ,"-y","nfs-kernel-server"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                
                # echo /etc/exports configuration
                command = f"echo '/root/nfsroot {jetson_ip}(async,rw,no_root_squash,no_all_squash,no_subtree_check,insecure,anonuid=1000,anongid=1000)' > /etc/exports"

                # Construct the lxc exec command
                lxc_command = f"lxc exec {vm_name} -- sh -c \"{command}\""
                print(lxc_command)
                # Execute the command using subprocess.run()

                try:
                    result = subprocess.run(lxc_command , shell=True, capture_output=True, text=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)

                # Refresh exported NFS configuration to NFS service

                command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "exportfs" ,"-a" ]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                #Restart and enable nfs service
                command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "systemctl" ,"restart" ,"nfs-kernel-server" ]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "systemctl" ,"enable" ,"nfs-kernel-server" ]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                # Install binutils to Image extraction (gzip format)
                command_librray_install=   ["lxc", "exec", vm_name, "--",  "apt" ,"install" ,"-y" ,"binutils" ]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
    
               




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


# print(user_info)


# Extracting the information
macvlan_name = user_info["macvlan_interface"]
user_name = user_info["user_name"]
macvlan_ip_addr = user_info["macvlan_ip_addr"]
nfs_ip_addr = user_info["nfs_ip_addr"]

# interface name on which macvlan is to be created
interface_name = "enp2s0"
macvlan_manager = MacVlan(interface_name)
vm_manager = VmManager()
vm_name="ferna"
ip_addr = IpAddr()



#vm_manager.set_nfs_ip_addr(vm_name ,"192.168.90.1/24")
#vm_manager.install_library_for_flashing_jetson(vm_name,"192.168.20.10/24")

#---------------
# # create vm for user
#vm_manager.create_user_vm(ubuntu_version, vm_name, root_size)

# # macvlan

# print(macvlan_ip_addr)

# vm_manager.create_macvlan_for_vm(macvlan_manager, macvlan_name)

# vm_manager.attach_macvlan_to_vm(vm_name, macvlan_name)

# res = vm_manager.interface_check(vm_name, "enp6s0")
# print(res)

# vm_manager.set_nfs_ip_addr(vm_name, nfs_ip_addr)
#----------------

#vm_manager.delete_vm(vm_name)
# vm_manager.delete_macvlan_for_vm(macvlan_manager, macvlan_name)



