import subprocess
import os 
import time 
import json 
class Jetson:

    def __init__(self):
        self.xavier_id = "ID 0955:7e19 NVIDIA Corp. APX"
        self.xavier_id_product = "7e19"
        self.number_xavier = 0


    def get_xavier_instances(self):
        # List to store detected Xavier USB instances
        xavier_usb_instance = []

        # Get the number of connected Jetson Xavier devices
        number_jetsons = self.number_of_jetsons_xavier_connected()

        # If no devices are connected, log and exit
        if number_jetsons == 0:
            print("No Jetson Xavier devices connected")
            return []

        # Command to find USB instances matching the Xavier ID
        command = f"grep {self.xavier_id_product} /sys/bus/usb/devices/*/idProduct"

        # Run the command and capture output
        try:
            instances = subprocess.run(
                command, capture_output=True, shell=True, text=True, check=True
            )

            # Filter the output to get USB instances
            usb_instances = instances.stdout.split("\n")
            usb_instances = [instance.split("/")[-2] for instance in usb_instances if instance]
            xavier_usb_instance.extend(usb_instances)

        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
            return []

        # Fixed switch interfaces (e.g., FastEthernet0/1, FastEthernet0/2, ...)
        switch_interfaces = [
            "FastEthernet0/1",
            "FastEthernet0/2",
            "FastEthernet0/3",
            "FastEthernet0/4"
        ]

        # Generate the list of Xavier instances with their properties
        xavier_instances = []
        for idx, usb_instance in enumerate(xavier_usb_instance):
            name = f"Jetson Xavier {idx + 1}"
            switch_interface = switch_interfaces[idx] if idx < len(switch_interfaces) else "UnknownInterface"
            xavier_instances.append(
                {
                    "name": name,
                    "switch_interface": switch_interface,
                    "usb_instance": usb_instance,
                }
            )

                # Write the xavier_instances to the resource file
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
        file_path = os.path.join(script_path, 'resource.json')

        try:
            with open(file_path, 'w') as file:
                json.dump(xavier_instances, file, indent=4)
                print(f"Updated resource.json with Xavier instances: {xavier_instances}")
        except Exception as e:
            print(f"Error writing to resource file: {e}")

        return xavier_instances
    def get_xavier_instances_v1(self):

        xavier_usb_instance = []
        number_jetsons = self.number_of_jetsons_xavier_connected()
        
        if number_jetsons == 0:
            print("No jetsons connected")
            return

        else:
            command = f"grep {self.xavier_id_product} /sys/bus/usb/devices/*/idProduct"
            
            instances = subprocess.run(command, capture_output= True, 
                                                shell = True,
                                                text=True,
                                                check = True)


            #xavier_usb_instance = instances.stdout.split("/")[5]

            usb_instances = instances.stdout.split("\n")
            usb_instances = [instance for instance in usb_instances if instance]

            for instance in usb_instances:
                instance = instance.split("/")[5]
                xavier_usb_instance.append(instance)



            return xavier_usb_instance


    def number_of_jetsons_xavier_connected(self):
        number_devices = 0
        xavier_instances = []
        command = "lsusb"
        usb_devices = subprocess.run(command, capture_output= True, text=True, check = True)
        usb_devices = usb_devices.stdout.splitlines()

        for device in usb_devices:
            device = device.split(":",1)[1].strip()
            if device == self.xavier_id:
                number_devices = number_devices + 1

        if number_devices == 0:
            print("No Jetson Xavier connected")

            return number_devices

        else:  

            return number_devices

    def flash_jetson_v1 (self, vm_name , nfs_ip_addres ):
         # Flash the Jetson
        nfs_ip_addres= nfs_ip_addres.split('/')[0]
        print(nfs_ip_addres)        
        command_librray_install=   ["lxc", "exec", vm_name, "--", "/root/Linux_for_Tegra/flash.sh" ,"-N",F"{nfs_ip_addres }:/root/nfsroot","--rcm-boot","jetson-xavier-nx-devkit-emmc" ,"eth0"]
        print("command",command_librray_install)
        try:
            result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
            print("STDOUT:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Failed to execute command:", e)
            print("STDOUT:\n", e.stdout)
            print("STDERR:\n", e.stderr)
            return
        
    def flash_jetson_v1 (self, nfs_ip_addres ,nfspath,parentpath):
            # Flash the Jetson
        nfs_ip_addres= nfs_ip_addres.split('/')[0]
        print(nfs_ip_addres)        
        command_librray_install=   [F" {parentpath}Linux_for_Tegra/flash.sh" ,"-N",F"{nfs_ip_addres }:/{nfspath}","--rcm-boot","jetson-xavier-nx-devkit-emmc" ,"eth0"]
        print("command",command_librray_install)
        try:
            result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
            print("STDOUT:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Failed to execute command:", e)
            print("STDOUT:\n", e.stdout)
            print("STDERR:\n", e.stderr)
            return
    def flash_jetson(self,nfs_ip_address, nfspath, usb_instance):
            # Get the directory of the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))

            # Define the parent directory
            parentpath = os.path.join(script_dir, '../api', 'jetson')
            
            # Define the working directory based on the parentpath
            working_directory = os.path.join(parentpath, 'Linux_for_Tegra')

            # Extract the NFS IP address
            net = nfs_ip_address.split('/')[0]
            ips = net.split(".")
            base_ip = '.'.join(ips[:3])
            subnet_low = str(int(ips[3]) + 2)
            subnet_up = str(int(ips[3]) + 5)

            # Construct the NFS target
            nfs_target = f"{net}:/{nfspath}"
            
            # Define the command
            command = [
                'sudo', './flash.sh', '--usb-instance', usb_instance, '-N', nfs_target, '--rcm-boot', 'jetson-xavier-nx-devkit-emmc', 'eth0'
            ]

            try:
                # Run the flash command
                process = subprocess.Popen(command, cwd=working_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                # Print the stdout and stderr in real-time
                stdout_lines = []
                stderr_lines = []
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        stdout_lines.append(output.strip())
                        print(output.strip())
                
                # Capture any remaining output
                stdout, stderr = process.communicate()
                stdout_lines.extend(stdout.splitlines())
                stderr_lines.extend(stderr.splitlines())
                
                # Check if the command was successful
                if process.returncode == 0:
                    print("Command executed successfully")
                    flash_success = True
                    # Wait for a specific period after a successful flash
                    time.sleep(2)  # Sleep for 2 seconds (adjust as needed)
                else:
                    print(f"Command execution failed with return code {process.returncode}")
                    flash_success = False
                    return {
                        "flashSucess": False,
                        "ip_address": None,
                        "wait_status": "Failed"
                    }
                
                # Generate IP addresses to test based on the provided range
                """tested_ips = [f"{base_ip}.{i}" for i in range(int(subnet_low), int(subnet_up) + 1)]

                # Test the IP addresses and return the first reachable one
                ip_address = None
                for ip in tested_ips:
                    if Jetson.ping(ip):
                        ip_address = ip
                        break
                """
                return {
                    "flashSucess": flash_success,
                    "ip_address": "ip_address",
                    "wait_status": "Completed"
                }
            
            except Exception as e:
                print(f"An error occurred: {e}")
                return {
                    "flashSucess": False,
                    "ip_address": None,
                    "wait_status": "Error"
                }
        
    
    def ping(ip):
        try:
            # Use the system ping command to check if the IP address is reachable
            output = subprocess.run(
                ["ping", "-c", "15", str(ip)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return output.returncode == 0
        except Exception as e:
            print(f"An error occurred during ping test: {e}")
            return False
jetson = Jetson()
#jetson.flash_jetson("10.111.138.4/24","/root/nfsroot/jetson1/rootfs",'1-2.3')
#number = jetson.number_of_jetsons_xavier_connected()

print(jetson.get_xavier_instances())
#sudo ./flash.sh -N 10.111.36.4:/root/nfsroot/rootfs --rcm-boot jetson-xavier-nx-devkit-emmc eth0 
#sudo ./flash.sh --usb-instance '1-2.3'  -N 10.111.138.4:/root/nfsroot/jetson1/rootfs  --rcm-boot jetson-xavier-nx-devkit-emmc eth0 