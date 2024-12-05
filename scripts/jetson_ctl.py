import subprocess
import os 
import time 
class Jetson:

    def __init__(self):
        self.xavier_id = "ID 0955:7e19 NVIDIA Corp. APX"
        self.xavier_id_product = "7e19"
        self.number_xavier = 0



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
#jetson.flash_jetson("10.111.217.4/24","/root/nfsroot/rootfs",'3-3.3')
number = jetson.number_of_jetsons_xavier_connected()

#print(jetson.get_xavier_instances())