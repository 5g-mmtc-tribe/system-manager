import subprocess
import time
from network_interface import NetworkInterface
import json
import os ,sys
import pylxd
from macvlan import MacVlan
# Get the absolute path of the parent directory
script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts'))
sys.path.append(script_path)
from ip_addr_manager import IpAddr
user_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../user-scripts'))
switch_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../switch'))
sys.path.append(switch_path)
from switch_manager import SwitchManager

class VmManager():
    # Get the absolute path to the resource.json file
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, '../data')
    jetson_path =  os.path.join(data_dir, 'jetson')
    bsp_path = os.path.join(data_dir, 'jetson_linux_r35.4.1_aarch64.tbz2')
    rootfs_path = os.path.join(data_dir, 'tegra_linux_sample-root-filesystem_r35.4.1_aarch64.tbz2')

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
    def is_vm_stopped(self, vm_name):
        # Command to check if the instance is running
        list_command = ["lxc", "list", vm_name, "--format", "json"]
        
        try:
            result = subprocess.run(list_command, capture_output=True, text=True, check=True)
            instances = json.loads(result.stdout)
            
            if instances and instances[0]["name"] == vm_name and instances[0]["status"] == "stopped":
                return True
            else:
                return False
        except subprocess.CalledProcessError as e:
            print("Failed to execute command:", e)
            print("STDOUT:\n", e.stdout)
            print("STDERR:\n", e.stderr)
            return False
    def start_vm(self, vm_name):
        if  not  self.is_vm_running(vm_name):
            #check if the vm already runnig 
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
        else :
               print("VM",vm_name," is alerady Runnig !")

    def stop_vm(self, vm_name):
        if  not  self.is_vm_stopped(vm_name):
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
        else :
               print("VM",vm_name," is alerady stopped!")

    def get_vm_ip(self ,vm_name):
        # Connect to LXD
        client = pylxd.Client()

        # Get the VM object
        vm = client.virtual_machines.get(vm_name)

        # Get the VM status and inspect its network information
        vm_info = vm.state()
        network_info = vm_info.network
        print("try get ip of vm ")
        # Extract IP address from network information
        ip_addresses = ""
        interface ="enp5s0"
        for ip in network_info[interface].get('addresses', []):
            if ip.get('family') == 'inet':
                ip_addresses=(ip.get('address'))

        return ip_addresses
    def check_vm_exists(self,vm_name):
        # Connect to the local LXD server
        client = pylxd.Client()
    
        # Get the list of all instances (containers and VMs)
        instances = client.instances.all()

        # Check if the specified VM exists
        for instance in instances:
            if instance.name == vm_name and instance.type == 'virtual-machine':
                return True
        return False
    def create_user_vm(self, ubuntu_version, vm_name, root_size):
        # check if vm exist already 
        vm_ma = VmManager()
        if vm_ma.check_vm_exists(vm_name):
            print("vm Exist ! ")
            return({"created":False})
        # Construct the command using an f-string
        command = f"lxc launch ubuntu:{ubuntu_version} {vm_name} --vm --device root,size={root_size} -c limits.cpu=4 -c limits.memory=4GiB"
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



    def create_macvlan_for_vm(self, macvlan_manager, macvlan_name,macvlan_ip_addr) :

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


    def set_nfs_ip_addr(self, vm_name, nfs_ip_addr,user_vlan_ip ,network_id ,switch_config):
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
            """command_add_ip = ["lxc", "exec", vm_name, "--", "ip", "addr", "add", nfs_ip_addr, "dev", interface_name]
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
                print("STDERR:\n", e.stderr)"""
            # set the ip of the nfs 
            ip = IpAddr()
             
             

            # add vlan interface 
            # Define the LXC command to add the NIC device
            command1 = ["lxc", "config", "device", "add", vm_name, "eth2", "nic", f"nictype=macvlan", f"parent=eno3", f"vlan={network_id}"]
            # Run the first LXC command
            VmManager.run_command(command1, f"Adding eth2 NIC to LXC vm '{vm_name}' with MACVLAN and VLAN {network_id}")
            device = switch_config
            switch = SwitchManager(device_type = device['device_type'],
                                ip = device['ip'],
                                port = device['port'],
                                password = device['password'])
            
            switch.configure_vlan(network_id,"vlan"+str(network_id))

            ip.update_network_config("ipconfig.txt", nfs_ip_addr ,user_vlan_ip)
            # set up  the nfs ip address
            command_librray_install=   ["sudo","lxc", "file","push" ,"ipconfig.txt" ,vm_name+"/root/"]
            VmManager.run_command(command_librray_install,"copy nfs ip address config")
            time.sleep(7)
            command = "sudo cat /root/ipconfig.txt > /etc/netplan/50-cloud-init.yaml"

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

                print("STDERR:\n", e.stderr)
             # Step 1: Disable cloud-init network configuration
            disable_cloud_init_cmd = [
                "lxc", "exec", vm_name, "--", "sudo", "sh", "-c", 
                "echo 'network: {config: disabled}' > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg"
            ]
            try:
                # Disable cloud-init network configuration
                subprocess.run(disable_cloud_init_cmd, capture_output=True, text=True, check=True)
                print("Disabled cloud-init network configuration.")
            except subprocess.CalledProcessError as e:
                # Handle errors during the command execution
                print("Failed to execute command:", e)
                print("Return code:", e.returncode)
                print("STDOUT:\n", e.stdout)
                print("STDERR:\n", e.stderr)

            command_net_apply = ["lxc", "exec", vm_name, "--", "sudo", "netplan", "apply"]
            print("Executing command:", " ".join(command_net_apply))
            
            try:
                # Execute the command
                result = subprocess.run(command_net_apply, capture_output=True, text=True, check=True)
                
                # Wait for a few seconds to let the changes take effect
                time.sleep(7)
                
                # Print the standard output and standard error
                print("Command executed successfully.")
                print("STDOUT:\n", result.stdout)
                print("STDERR:\n", result.stderr)
            except subprocess.CalledProcessError as e:
                # Handle errors during the command execution
                print("Failed to execute command:", e)
                print("Return code:", e.returncode)
                print("STDOUT:\n", e.stdout)
                print("STDERR:\n", e.stderr)

    def run_command(command, description):
            print(f"Running: {description}")
            print(f"Command: {' '.join(command)}")

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            stderr = process.communicate()[1]
            if stderr:
                print(stderr)
                        # Check if the command was successful
            if process.returncode == 0:
                print("Command executed successfully")
            else:
                  error_message = f"Command execution failed with return code {process.returncode}"
                  raise Exception(error_message)


    def configure_vm_nat(self, vm_name, src_script_path):
        """
        Configures the LXC VM by enabling IP forwarding, setting up NAT, and copying a script to the VM.
        
        :param vm_name: Name of the LXC VM
        :param src_script_path: Path to the script on the host to be copied to the VM
        """
        # Commands to be executed inside the LXC VM
        commands = [
            'sysctl -w net.ipv4.ip_forward=1',
            'iptables -t nat -A POSTROUTING -o enp5s0 -j MASQUERADE',
            'apt-get install iptables-persistent -y',
            
        ]
        #'netfilter-persistent save -y',
        #   'netfilter-persistent reload -y'
        try:
            # Execute commands in the LXC VM
            for cmd in commands:
                subprocess.run(['lxc', 'exec', vm_name, '--', 'sh', '-c', cmd], check=True)
                print(f"Command '{cmd}' executed successfully in {vm_name}")

            # Copy the script to the LXC VM
            subprocess.run(['lxc', 'file', 'push', src_script_path, f'{vm_name}/root/install_torch'], check=True)
            print(f"File copied successfully to {vm_name}:/root/install_torch")
        
        except subprocess.CalledProcessError as e:
            print(f"Error during configuration: {e}")

    def create_dhcp_server(self ,vm_name,nfs_ip_addr):
            # install  the  DHCP server 
            command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "apt" ,"install" ,"-y","isc-dhcp-server"]
            VmManager.run_command(command_librray_install,"install  the  DHCP server")
            # set up  the dhcp server config file 
                        # set the ip of the nfs 
            ip = IpAddr()
            ip.update_dhcp_configuration("dhcpConfig.txt", nfs_ip_addr)
            command_librray_install=   ["sudo","lxc", "file","push" ,"dhcpConfig.txt" ,vm_name+"/root/"]
            VmManager.run_command(command_librray_install,"copy dhcp config")
            
            command = "sudo cat /root/dhcpConfig.txt >> /etc/dhcp/dhcpd.conf"
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
            #Restart and enable dhcp server
            command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "systemctl" ,"restart" ,"isc-dhcp-server" ]
            VmManager.run_command(command_librray_install,"Restart  dhcp server")
            command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "systemctl" ,"enable" ,"isc-dhcp-server" ]
            VmManager.run_command(command_librray_install,"enable dhcp server")

    def create_nfs_server(self ,vm_name ,nfs_ip_addres):
            #ip_addr = IpAddr()
            #jetson_ip=ip_addr.jetson_ip(nfs_ip_addres)

            # Create NFS folder to be used on the Jetson (on the VM)
            vmcommand =["lxc", "exec", vm_name, "--", "sudo"]
            command_librray_install=   vmcommand +["mkdir" ,"/root/nfsroot" ]
            VmManager.run_command(command_librray_install,"Create NFS folder to be used on the Jetson (on the VM)")
            
            vmcommand =["lxc", "exec", vm_name, "--"]
            command_librray_install = vmcommand +["chown","-R" ,"nobody:nogroup", "/root/nfsroot"]
            VmManager.run_command(command_librray_install,"change nfs folder previliges")
            command_librray_install = vmcommand+["sudo" ,"chmod" ,"755", "/root/nfsroot"]
            VmManager.run_command(command_librray_install,"change nfs folder previliges)")

            # Rsync original "rootfs" to "nfsroot"
            vmcommand =["lxc", "exec", vm_name, "--"]
            #command_librray_install=   vmcommand +["sudo","rsync" ,"-aAXv" ,"jetson/Linux_for_Tegra/rootfs/" ,"/root/nfsroot"]
            #command_librray_install=["sudo","lxc", "file","push" ,"-r","jetson/Linux_for_Tegra/rootfs/" ,vm_name+"/root/nfsroot"] 
            # Define the command to run
            """ command = [
                'sudo', 'lxc', 'file', 'push', '-r', 'jetson/Linux_for_Tegra/rootfs/', 'mehdivm/root/nfsroot'
            ]"""
            command = [ 'sudo' , 'lxc'  ,"exec" , vm_name , "--" , "wget", "http://193.55.250.148/rootfs-noeula-user.tar.gz"]
            print(command)
            # Execute the command using subprocess.run()
            try:
                result = subprocess.run(command,  capture_output=True, text=True, check=True)
                print("STDOUT:", result.stdout)
            except subprocess.CalledProcessError as e:
                print("Failed to execute command:", e)
                print("STDOUT:\n", e.stdout)
                print("STDERR:\n", e.stderr)
            command = [ 'sudo' , 'lxc'  ,"exec" , vm_name , "--" , "tar" ,"xpzf","/root/rootfs-noeula-user.tar.gz" ,"-C", "/root/nfsroot/"]
            print(command)
            # Execute the command using subprocess.run()
            try:
                result = subprocess.run(command,  capture_output=True, text=True, check=True)
                print("STDOUT:", result.stdout)
            except subprocess.CalledProcessError as e:
                print("Failed to execute command:", e)
                print("STDOUT:\n", e.stdout)
                print("STDERR:\n", e.stderr)
            # Setting up the NFS server inside the VM
            command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "apt" ,"install" ,"-y","nfs-kernel-server"]
            VmManager.run_command(command_librray_install,"Setting up the NFS server inside the VM")
            # echo /etc/exports configuration
            command = f"echo '/root/nfsroot/rootfs *(async,rw,no_root_squash,no_all_squash,no_subtree_check,insecure,anonuid=1000,anongid=1000)' > /etc/exports"
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
            VmManager.run_command(command_librray_install,"Refresh exported NFS configuration to NFS service")
            #Restart and enable nfs service
            command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "systemctl" ,"restart" ,"nfs-kernel-server" ]
            VmManager.run_command(command_librray_install,"enable nfs service")
            command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "systemctl" ,"enable" ,"nfs-kernel-server" ]
            VmManager.run_command(command_librray_install," Restart nfs service")


    def download_Jetson_driver():

                #installing the bzip2 package
                command_librray_install = [ "sudo", "apt-get", "install", "bzip2"]
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
                command_librray_install = [ "sudo", "add-apt-repository","-y" ,"universe"]
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
                command_librray_install = [ "sudo","apt-get" ,"update"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                # Create jeston folder
                command_librray_install=  ["sudo" , "mkdir" ,"jetson" ]

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
                command_librray_install = ["sudo", "tar","-xf" ,VmManager.bsp_path ,"-C","jetson"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout) 
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                command_librray_install = ["tar", "xpf" ,VmManager.rootfs_path, "-C","jetson/Linux_for_Tegra/rootfs/"]
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
                command_librray_install = ["sudo", "apt-get", "install", "qemu-user-static"]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                
                script_path = "jetson/Linux_for_Tegra/apply_binaries.sh"
                print("command",script_path )
                try:
                    # Run the script
                    result = subprocess.run(["sudo","bash", script_path], capture_output=True, text=True)
                    #result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                #installing the libraries for  flashing the jetson
                command_librray_install = [ "sudo",   "apt-get", "install", "-y" ,"lz4" ]
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return
                
                command_librray_install=   ["sudo", "apt-get" ,"install" ,"libxml2-utils"]
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
                command_librray_install=   [ "sudo", "jetson/Linux_for_Tegra/tools/l4t_create_default_user.sh" ,'-u' ,vm_name,'-p',vm_name ,'-n',vm_name,'--accept-license']
                print("command",command_librray_install)
                try:
                    result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
                    print("STDOUT:", result.stdout)
                except subprocess.CalledProcessError as e:
                    print("Failed to execute command:", e)
                    print("STDOUT:\n", e.stdout)
                    print("STDERR:\n", e.stderr)
                    return

    def install_library_for_flashing_jetson(_self ,vm_name ,nfs_ip_addr ) :
            #VmManager.download_Jetson_driver()
            vm_manager = VmManager()
            command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "apt" ,"update" ]
            VmManager.run_command(command_librray_install,"update apt")
            # copy  5gmmtool file 
            command_librray_install=   ["sudo","lxc", "file","push" ,user_script_path+"/5gmmtctool" ,vm_name+"/root/"]
            VmManager.run_command(command_librray_install,"copy 5gmmtctool ")
            vm_manager.create_nfs_server(vm_name=vm_name,nfs_ip_addres= nfs_ip_addr)
            vm_manager.create_dhcp_server(vm_name,nfs_ip_addr)
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
             # configure Nat 
            vm_manager.configure_vm_nat(vm_name,"install_torch.sh")

    def install_5gmmtctool(_self ,vm_name , nfs_ip_addr):
            # copy dhcp config 
            ip = IpAddr()
            ip.update_dhcp_configuration("dhcpConfig.txt", nfs_ip_addr)
            command_librray_install=   ["sudo","lxc", "file","push" ,"dhcpConfig.txt" ,vm_name+"/root/"]
            VmManager.run_command(command_librray_install,"copy dhcp config")
            # copy  5gmmtool file 
            command_librray_install=   ["sudo","lxc", "file","push" ,user_script_path+"/5gmmtctool" ,vm_name+"/root/"]
            VmManager.run_command(command_librray_install,"copy 5gmmtctool ")
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
vm_name="mehdivm"
ip_addr = IpAddr()

#print(vm_manager.get_vm_ip("debbah"))
#vm_manager.install_5gmmtctool("debbah" ,"")

#vm_manager.set_nfs_ip_addr(vm_name ,"192.168.90.1/24")#
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



