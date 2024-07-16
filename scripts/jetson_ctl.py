import subprocess

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
        
    def flash_jetson (self, vm_name , nfs_ip_addres ,nfspath,parentpath):
            # Flash the Jetson
        nfs_ip_addres= nfs_ip_addres.split('/')[0]
        print(nfs_ip_addres)        
        command_librray_install=   [F" {parentpath}Linux_for_Tegra/flash.sh" ,"-N",F"{nfs_ip_addres }:{nfspath}","--rcm-boot","jetson-xavier-nx-devkit-emmc" ,"eth0"]
        print("command",command_librray_install)
        try:
            result = subprocess.run(command_librray_install , capture_output=True, text=True, check=True)
            print("STDOUT:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Failed to execute command:", e)
            print("STDOUT:\n", e.stdout)
            print("STDERR:\n", e.stderr)
            return
#jetson = Jetson()
#jetson.flash_jetson(" 192.168.0.10/24")
#number = jetson.number_of_jetsons_xavier_connected()

#print(jetson.get_xavier_instances())