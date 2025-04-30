import subprocess
import os 
import time 
import json 
import logging
from config import RESOURCE_JSON_PATH
# Setup module-level logger
logger = logging.getLogger(__name__)
class Jetson:

    def __init__(self):
        self.xavier_id = "ID 0955:7e19 NVIDIA Corp. APX"
        self.xavier_id_product = "7e19"
        self.number_xavier = 0
        self.orin_id = "ID 0955-7323 NVIDIA Corp. APX"
        self.xavier_kit ="jetson-xavier-nx-devkit"
        self.orin_kit ="jetson-orin-nano-devkit"
        # self.orin_kit ="jetson-orin-nano-devkit-nvme"
        self.nano_kit ="jetson-nano-devkit-emmc"
        self .TEGRA_3274 ="Linux_for_Tegra_jp3274"
        self .TEGRA_3541 = "Linux_for_Tegra_jp3541"

    def get_xavier_instances_v2(self):
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
            name = f"j20-tribe{idx + 1}"
            switch_interface = switch_interfaces[idx] if idx < len(switch_interfaces) else "UnknownInterface"
            xavier_instances.append(
                {
                    "name": name,
                    "switch_interface": switch_interface,
                    "usb_instance": usb_instance,
                }
            )

                # Write the xavier_instances to the resource file

        file_path = RESOURCE_JSON_PATH

        try:
            with open(file_path, 'w') as file:
                json.dump(xavier_instances, file, indent=4)
                print(f"Updated resource.json with Xavier instances: {xavier_instances}")
        except Exception as e:
            print(f"Error writing to resource file: {e}")

        return xavier_instances
    def get_xavier_instances(self):

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

     
    def flash_jetson(self, nfs_ip_address, nfspath, usb_instance, model, nvidia_id):

        
        # Select the correct kit based on the model
        if model == "Jetson-Xavier-NX":
            kit = self.xavier_kit
            tegra_folder= self.TEGRA_3541
            rcm = '--rcm-boot'
        elif model == "Jetson-Orin-NX":
            kit = self.orin_kit
            tegra_folder= self.TEGRA_3541
            rcm = '--rcm-boot'
        elif model == "Jetson-Nano":
            kit = self.nano_kit
            tegra_folder= self.TEGRA_3274
            rcm = ''
        else:
            print("Unknown model provided")
            return {
                "flashSucess": False,
                "ip_address": None,
                "wait_status": "Error: Unknown model"
            }

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Define the parent directory
        parentpath = os.path.join(script_dir, '../api', 'jetson')
        
        # Define the working directory based on the parentpath
        working_directory = os.path.join(parentpath, tegra_folder)

        # Extract the NFS IP address
        net = nfs_ip_address.split('/')[0]
        
        # Construct the NFS target
        nfs_target = f"{net}:/{nfspath}"
        # Define the command using the selected kit
        command = [
            'sudo', './flash.sh', '--usb-instance', usb_instance, '-N', nfs_target,
            rcm, kit, 'eth0'
        ]
        logging.info("Flash jetson command: %s", command)
        try:
            # Run the flash command
            process = subprocess.Popen(command, cwd=working_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Print the stdout in real-time
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
                time.sleep(2)  # Sleep for 2 seconds (adjust as needed)
            else:
                print(f"Command execution failed with return code {process.returncode}")
                flash_success = False
                return {
                    "flashSucess": False,
                    "ip_address": None,
                    "wait_status": "Failed"
                }
            
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
#jetson = Jetson()
#jetson.flash_jetson("10.111.67.4/24","/root/nfsroot-jp-3541/rootfs",'1-4.3',"Jetson-Orin-NX","")    
#number = jetson.number_of_jetsons_xavier_connected()

#print(jetson.get_xavier_instances())
#sudo ./flash.sh -N 10.111.36.4:/root/nfsroot/rootfs --rcm-boot jetson-xavier-nx-devkit-emmc eth0 
#sudo ./flash.sh --usb-instance '1-4.3'  -N 10.111.67.4:/root/nfsroot-jp-3541/rootfs  --rcm-boot jetson-orin-nano-devkit-nvme eth0 
#sudo ./flash.sh --usb-instance '1-4.1.4'  -N 10.111.67.4:/root/nfsroot-jp-3274/rootfs  --rcm-boot jetson-nano-emmc eth0 
#sudo ./flash.sh --usb-instance '1-4.1.2'  -N 10.111.67.4:/root/nfsroot-jp-3274/rootfs  --rcm-boot jetson-nano-emmc eth0 