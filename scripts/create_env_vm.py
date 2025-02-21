import subprocess
import time
from network_interface import NetworkInterface
import json
import os ,sys
import pylxd
import redis
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
    nbd_size= 30384
    ###  helper #####
    def run_lxc_command(vm_name, command):
        """Runs a command inside an LXC VM."""
        full_command = ["lxc", "exec", vm_name, "--"] + command
        try:
            subprocess.run(full_command, check=True, text=True)
            print(f"✅ Command succeeded: {' '.join(command)}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(command)}\nError: {e}")
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
    def is_interface_up(self,vm_name, interface_name="enp5s0"):
        """Check if a specific network interface is present and up."""
        check_interface_command = ["lxc", "exec", vm_name, "--", "ip", "-c", "a"]

        try:
            # Run the command to list network interfaces
            result = subprocess.run(check_interface_command,
                                    capture_output=True,
                                    text=True,
                                    check=True)

            # Check if the interface name is in the output
            if interface_name in result.stdout:
                return True  # Interface is up
            else:
                return False  # Interface is not up

        except subprocess.CalledProcessError as e:
            # Return False on any error but don't print error every time
            return False

    def start_vm(self, vm_name):
        """Start the VM and wait until the network interface is up."""
        if not self.is_vm_running(vm_name):
            print(f"Starting VM {vm_name}...")
            subprocess.run(['lxc', 'start', vm_name], check=True)

            # Wait for the network interface to be up
            timeout = 30  # Maximum wait time in seconds
            interval = 2  # Polling interval in seconds
            
            start_time = time.time()  # Track the start time

            # Polling loop until the interface is up or timeout is reached
            while time.time() - start_time < timeout:
                if self.is_interface_up(vm_name, "enp6s0"):  # Check if the interface is up
                    print(f"VM {vm_name} is now running with an active network interface.")
                    self.configure_vm_nat(vm_name)
                    
                    return 0  # Success

                # Print waiting message only while the interface is not up
                print(f"Waiting for interface {vm_name} to come up...")
                time.sleep(interval)  # Wait before checking again

            # Timeout reached
            print(f"Warning: VM {vm_name} started, but the network interface is still down.")
            return 1  # Timeout occurred
        
        else:
            print(f"VM {vm_name} is already running!")
            return 0  # VM is already running

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



    def create_macvlan_for_vm_old(self, macvlan_manager, macvlan_name,macvlan_ip_addr) :

        if macvlan_manager.macvlan_exists(macvlan_name) == False:
            macvlan_manager.create_macvlan(macvlan_name)
            macvlan_manager.set_ip_addr(macvlan_ip_addr, macvlan_name)

        else:
            print("Macvlan for user exists")


    def create_macvlan_for_vm(self, vm_name ,network_id,switch_config,interface_name ,macvlan_name) :
        # add vlan interface 
        # Define the LXC command to add the NIC device
        command1 = ["lxc", "config", "device", "add", vm_name, 'eth2', "nic", f"nictype=macvlan", f"parent={interface_name}" , f"vlan={network_id}"]
        # Run the first LXC command
        VmManager.run_command(command1, f"Adding eth2 NIC to LXC vm '{vm_name}' with MACVLAN and VLAN {network_id}")
        device = switch_config
        switch = SwitchManager(device_type = device['device_type'],
                            ip = device['ip'],
                            port = device['port'],
                            password = device['password'])
        
        switch.configure_vlan(network_id,"vlan"+str(network_id))

  

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


    def set_nfs_ip_addr(self, vm_name, nfs_ip_addr ):
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
    
            # set the ip of the nfs 
            ip = IpAddr()
            ip.update_network_config("ipconfig.txt",nfs_ip_addr)
            # set up  the nfs ip address
            command_librray_install=   ["lxc", "file","push" ,"ipconfig.txt" ,vm_name+"/root/"]
            VmManager.run_command(command_librray_install,"copy nfs ip address config")
            time.sleep(7)
            command = "cat /root/ipconfig.txt > /etc/netplan/50-cloud-init.yaml"

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


    def add_torch_script(self, vm_name, src_script_path):
        """
        add_torch_script
        """
        try:

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
            command_librray_install=   ["lxc", "file","push" ,"dhcpConfig.txt" ,vm_name+"/root/"]
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
            command_librray_install=   vmcommand +["mkdir" ,"/root/nfsroot/rootfs" ]
            VmManager.run_command(command_librray_install,"Create rootfs folder to be used on the Jetson (on the VM)")
            
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
            command = [  'lxc'  ,"file" ,"push","rootfs-basic-jp3541-noeula-user.tar.gz",vm_name+"/root/"]
            print(command)
            # Execute the command using subprocess.run()
            try:
                result = subprocess.run(command,  capture_output=True, text=True, check=True)
                print("STDOUT:", result.stdout)
            except subprocess.CalledProcessError as e:
                print("Failed to execute command:", e)
                print("STDOUT:\n", e.stdout)
                print("STDERR:\n", e.stderr)
            command = [ 'lxc'  ,"exec" , vm_name , "--" , "tar" ,"xpzf","/root/rootfs-basic-jp3541-noeula-user.tar.gz" ,"-C", "/root/nfsroot/rootfs"]
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


    def configure_nbd_on_lxc_vm(self,vm_name, nfs_server_ip):
            """Configures NBD inside an LXC VM from the LXC host."""
            
            print(f"🔧 Setting up NBD inside LXC VM: {vm_name}")

            # Install NBD server
            VmManager.run_lxc_command(vm_name, ["apt", "update"])
            VmManager.run_lxc_command(vm_name, ["apt", "install", "-y", "nbd-server"])

            # Load the NBD kernel module and ensure it persists
            VmManager.run_lxc_command(vm_name, ["modprobe", "nbd"])
            VmManager.run_lxc_command(vm_name, ["sh", "-c", "echo 'nbd' >> /etc/modules"])

            # Create NBD directory with correct permissions
            VmManager.run_lxc_command(vm_name, ["mkdir", "-p", "/root/nbd_jetson"])
            VmManager.run_lxc_command(vm_name, ["chmod", "755", "/root/nbd_jetson"])

                # Define NBD configuration
            config_content = f"""[generic]
            allowlist = true

            [nbd_jetson]
            exportname = /root/nbd_jetson/nbd_jetson.img
            readonly = false
            listenaddr = {nfs_server_ip}
            """

            # Write configuration to /etc/nbd-server/config
            VmManager.run_lxc_command(vm_name, ["sh", "-c", f"echo '{config_content}' > /etc/nbd-server/config"])

            # Create the NBD image and format it
            VmManager.run_lxc_command(vm_name, ["dd", "if=/dev/zero", "of=/root/nbd_jetson/nbd_jetson.img", "bs=1M", "count="f"{VmManager().nbd_size}"])
            VmManager.run_lxc_command(vm_name, ["mkfs.ext4", "/root/nbd_jetson/nbd_jetson.img"])

            # Restart NBD service
            VmManager.run_lxc_command(vm_name, ["systemctl", "restart", "nbd-server"])

            print("🚀 NBD setup completed successfully inside the LXC VM!")
    def configure_vm_nat(self, vm_name):
        """
        Configures the LXC VM by enabling IP forwarding, setting up NAT, and copying a script to the VM.
        
        :param vm_name: Name of the LXC VM
        """
        # Commands to be executed inside the LXC VM
        commands = [
            'sysctl -w net.ipv4.ip_forward=1',
            'iptables -t nat -A POSTROUTING -o enp5s0 -j MASQUERADE',
            
            
        ]
        # 'apt-get install iptables-persistent -y',
        # 'netfilter-persistent save -y',
        #   'netfilter-persistent reload -y'
        try:
            # Execute commands in the LXC VM
            for cmd in commands:
                subprocess.run(['lxc', 'exec', vm_name, '--', 'sh', '-c', cmd], check=True)
                print(f"Command '{cmd}' executed successfully in {vm_name}")

        
        except subprocess.CalledProcessError as e:
            print(f"Error during configuration: {e}")
    # ---------------------------
    # Function: create_readme for jeston
    # ---------------------------
    def create_readme_in_vm(vm_name, nfs_ip_addr):
        """
        Creates a README.md file directly inside the VM with setup instructions.

        - vm_name: Name of the VM/container.
        - nfs_ip_addr: The NFS server IP address to include in the instructions.
        """
        """
        Creates a README.md file directly inside the VM using a here-document.
        
        Args:
          vm_name (str): Name of the VM/container.
          nfs_ip_addr (str): The NFS server IP address to include in the file.
        """
        nfs_ip_addr= nfs_ip_addr.split('/')[0]
        # Define the README content
        content = f"""# Setup Instructions

        Follow these steps to prepare your project:

        - Step 1: Run lib_setup.sh
        - This script installs all the necessary libraries.

        - Step 2: Run jetson_setup.sh with your NFS IP address
        - Command:
            ./jetson_setup.sh {nfs_ip_addr}
            
        - Replace {nfs_ip_addr} with your actual NFS IP address.
        """
         # Step 1: Create an empty README.md file in the VM.
        touch_command = f'''lxc exec {vm_name} -- bash -c "touch /root/nfsroot/rootfs/home/mmtc/README.md"'''
        print("Creating empty README.md in VM...")
        subprocess.run(touch_command, shell=True, check=True)   
# Step 3: Write the content into the README.md file using a here-document.
        write_command = (
            f'''lxc exec {vm_name} -- bash -c "cat > /root/nfsroot/rootfs/home/mmtc/README.md << 'EOF'
{content}
EOF"'''
        )
        print("Writing content to README.md in VM...")
        subprocess.run(write_command, shell=True, check=True)
        print("README.md has been created and populated in the VM.")
        

            
    def install_library_for_flashing_jetson(_self ,vm_name ,nfs_ip_addr ) :
            #VmManager.download_Jetson_driver()
            vm_manager = VmManager()
            command_librray_install=   ["lxc", "exec", vm_name, "--", "sudo", "apt" ,"update" ]
            VmManager.run_command(command_librray_install,"update apt")
            # copy  5gmmtool file 
            command_librray_install=   ["lxc", "file","push" ,user_script_path+"/5gmmtctool" ,vm_name+"/root/"]
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
            vm_manager.configure_vm_nat(vm_name)
            vm_manager.add_torch_script(vm_name,"install_torch.sh")
            # copy nfs setup for multi jetson
            command_librray_install=   ["lxc", "file","push" ,user_script_path+"/nfs_setup.sh" ,vm_name+"/root/"]
            VmManager.run_command(command_librray_install,"copy nfs setup for multi jetson ")
            # copy jetson setup script 
            command_librray_install=   ["lxc", "file","push" ,user_script_path+"/lib_setup.sh" ,vm_name+"/root/"]
            VmManager.run_command(command_librray_install,"copy jetson setup")
            command_librray_install = ["lxc", "file", "push", user_script_path+"/Dockerfile", vm_name+"/root/nfsroot/rootfs/home/mmtc/"]
            VmManager.run_command(command_librray_install, "copy Dockerfile user home")
            command_librray_install = ["lxc", "file", "push", user_script_path+"/lib_setup.sh", vm_name+"/root/nfsroot/rootfs/home/mmtc/"]
            VmManager.run_command(command_librray_install, "copy jetson setup to user home")
            command_librray_install = ["lxc", "file", "push", user_script_path+"/jetson_setup.sh", vm_name+"/root/nfsroot/rootfs/home/mmtc/"]
            VmManager.run_command(command_librray_install, "copy jetson setup")
            ## create a reade me for jetson
            VmManager.create_readme_in_vm(vm_name, nfs_ip_addr)
            # docker images 
            command = [  'lxc'  ,"file" ,"push","mmtc-docker.tar",vm_name+"/root/nfsroot/rootfs/home/mmtc/"]
            VmManager.run_command(command,"get docker images ")
            time.sleep(10)

    def add_ssh_key_to_lxd(self, username, lxd_vm_name):
        # Fixed index name
        index_name = 'UserIdxs'
        redis_client = redis.Redis(host='localhost', port=6379)

        # Search for the user in Redis using RediSearch
        search_results = redis_client.ft(index_name).search(f"@login:({username})")
        
        # Check if we got any results
        if not search_results.docs:
            raise ValueError(f"No user found with login: {username}")

        # Assuming the first result is the user we want (adapt as needed)
        user_data = search_results.docs[0].json
        user_data = json.loads(user_data)
        
        # Extract the SSH keys from the user data
        ssh_keys = user_data.get('user', {}).get('sshKeys', [])
        if not ssh_keys:
            raise ValueError("No SSH keys found for the user")

        # Join all keys into a single string (in case there are multiple keys)
        ssh_key_str = "\n".join(ssh_keys)
        
        # Define the path to the SSH directory and authorized_keys file
        ssh_dir = "/root/.ssh"
        authorized_keys_file = f"{ssh_dir}/authorized_keys"

        # Create the .ssh directory if it doesn't exist
        subprocess.run(['lxc', 'exec', lxd_vm_name, '--', 'bash', '-c', f'if [ ! -d "{ssh_dir}" ]; then mkdir -p "{ssh_dir}"; fi'], check=True)

        # Check if the key already exists in the authorized_keys file
        try:
            result = subprocess.run(
                ['lxc', 'exec', lxd_vm_name, '--', 'bash', '-c', f'cat {authorized_keys_file}'],
                capture_output=True, text=True, check=True
            )
            existing_keys = result.stdout.splitlines()
        except subprocess.CalledProcessError:
            # If the file doesn't exist or is inaccessible, assume no keys exist
            existing_keys = []

        # Add the key only if it's not already in the file
        new_keys = [key for key in ssh_keys if key not in existing_keys]

        if new_keys:
            keys_to_add = "\n".join(new_keys)
            subprocess.run(
                [ 'lxc', 'exec', lxd_vm_name, '--', 'bash', '-c', f'echo "{keys_to_add}" >> {authorized_keys_file}'],
                check=True
            )
            print(f"Added new SSH keys to {authorized_keys_file} in VM {lxd_vm_name}")
        else:
            print(f"No new SSH keys to add. All keys already exist in {authorized_keys_file}.")

        # Set correct permissions
        subprocess.run(['lxc', 'exec', lxd_vm_name, '--', 'chmod', '700', ssh_dir], check=True)
        subprocess.run(['lxc', 'exec', lxd_vm_name, '--', 'chmod', '600', authorized_keys_file], check=True)
        subprocess.run(['lxc', 'exec', lxd_vm_name, '--', 'chown', 'root:root', ssh_dir], check=True)
        subprocess.run(['lxc', 'exec', lxd_vm_name, '--', 'chown', 'root:root', authorized_keys_file], check=True)

        print(f"SSH key verification and update complete for VM {lxd_vm_name}.")

    def install_5gmmtctool(_self ,vm_name , nfs_ip_addr):
            # copy dhcp config 
            ip = IpAddr()
            ip.update_dhcp_configuration("dhcpConfig.txt", nfs_ip_addr)
            command_librray_install=   ["lxc", "file","push" ,"dhcpConfig.txt" ,vm_name+"/root/"]
            VmManager.run_command(command_librray_install,"copy dhcp config")
            # copy  5gmmtool file 
            command_librray_install=   ["lxc", "file","push" ,user_script_path+"/5gmmtctool" ,vm_name+"/root/"]
            VmManager.run_command(command_librray_install,"copy 5gmmtctool ")

    
    def setup_nfs_jetson(self,vm_name, device_names):
        """
        Launches the NFS setup script inside an LXC VM.

        :param vm_name: Name of the LXC virtual machine
        :param device_names: List of device names to pass as arguments to the script
        """
        if not vm_name or not device_names:
            print("Usage: launch_script_on_lxc_vm('<LXC_VM_NAME>', ['device1', 'device2', ...])")
            return

        script_path = "/root/nfs_setup.sh"
        device_args = " ".join(device_names)  # Convert device list to space-separated string
        vm_manager = VmManager()
        try:
            #vm_manager.start_vm(vm_name=vm_name)

            subprocess.run(["lxc", "exec", vm_name, "--", "chmod", "+x", script_path], check=True)
            print("Executing script inside LXC VM...")
            subprocess.run(["lxc", "exec", vm_name, "--", "bash", "-c", f"{script_path} {device_args}"], check=True)

            print(f"Script execution completed inside LXC VM: {vm_name}")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error: {e}")


def setup_jetson(base_dir, username, password, hostname):
    """
    Sets up Jetson environment by performing the following steps:
    1. Extract and prepare files from the given base directory.
    2. Apply binaries.
    3. Create a default user.
    4. Compress the root filesystem and place the tarball in the api directory.

    Parameters:
    - base_dir (str): Directory containing the Jetson tar files.
    - username (str): Username for the default user.
    - password (str): Password for the default user.
    - hostname (str): Hostname for the Jetson device.
    """
    try:
        # Define file paths
        jetson_tar = os.path.join(base_dir, "Jetson_Linux_R35.4.1_aarch64.tbz2")
        tegra_tar = os.path.join(base_dir, "Tegra_Linux_Sample-Root-Filesystem_R35.4.1_aarch64.tbz2")
        output_dir = os.path.join("api", "jetson")

        # Create api/jetson directory
        os.makedirs(output_dir, exist_ok=True)

        # Step 1: Extract Jetson Linux package
        print("Extracting Jetson Linux package...")
        subprocess.run(["sudo", "tar", "-xf", jetson_tar, "-C", output_dir], check=True)

        # Step 2: Extract Tegra root filesystem
        print("Extracting Tegra root filesystem...")
        tegra_rootfs = os.path.join(output_dir, "Linux_for_Tegra", "rootfs")
        os.makedirs(tegra_rootfs, exist_ok=True)
        subprocess.run(["sudo", "tar", "xpf", tegra_tar, "-C", tegra_rootfs], check=True)

        # Step 3: Apply binaries
        print("Adding universe repository and installing dependencies...")
        subprocess.run(["sudo", "add-apt-repository", "universe"], check=True)
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", "qemu-user-static"], check=True)

        print("Applying binaries...")
        apply_binaries_script = os.path.join(output_dir, "Linux_for_Tegra", "apply_binaries.sh")
        subprocess.run(["sudo", apply_binaries_script], check=True)

        # Step 4: Create default user
        print("Installing additional dependencies...")
        subprocess.run(["sudo", "apt-get", "install", "-y", "lz4", "libxml2-utils"], check=True)

        print("Creating default user...")
        create_user_script = os.path.join(output_dir, "Linux_for_Tegra", "tools", "l4t_create_default_user.sh")
        subprocess.run([
            "sudo", create_user_script,
            "-u", username, "-p", password, "-n", hostname, "--accept-license"
        ], check=True)

        # Step 5: Compress root filesystem
        print("Compressing root filesystem into rootfs-noeula-user.tar.gz...")
        rootfs_dir = os.path.join(output_dir, "Linux_for_Tegra", "rootfs")
        tarball_path = os.path.join("api", "rootfs-noeula-user.tar.gz")
        subprocess.run(["sudo", "tar", "czvf", tarball_path, "-C", rootfs_dir, "."], check=True)

        print(f"Root filesystem compressed successfully to {tarball_path}.")
        print("Jetson setup completed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error while running command: {e.cmd}")
        print(f"Output: {e.output}")
        raise

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
    }


# print(user_info)


# Extracting the information
macvlan_name = user_info["macvlan_interface"]
user_name = user_info["user_name"]
nfs_ip_addr = user_info["nfs_ip_addr"]

# interface name on which macvlan is to be created
interface_name = "enp2s0"   
macvlan_manager = MacVlan(interface_name)
vm_manager = VmManager()
vm_name="mehdivm"
ip_addr = IpAddr()
#VmManager.create_readme_in_vm("mehdi","10.111.67.4")
#vm_manager.configure_nbd_on_lxc_vm("mehdi","10.111.67.4")
#vm_manager.setup_nfs_jetson("mehdi",["j20-tribe4"])
#setup_jetson('data', 'iotuser', 'iotuser', 'iotuser')
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

#vm_manager.add_ssh_key_to_lxd("debbah","debbah")

