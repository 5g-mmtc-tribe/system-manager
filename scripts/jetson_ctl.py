import subprocess

class Jetson:

    def __init__(self):
        self.xavier_id = "ID 0955:7e19 NVIDIA Corp. APX"
        self.xavier_id_product = "7e19"
        self.number_xavier = 0



    def get_xavier_instances(self):
        
        command = f"grep {self.xavier_id_product} /sys/bus/usb/devices/*/idProduct"
        
        instances = subprocess.run(command, capture_output= True, 
                                            shell = True,
                                            text=True,
                                            check = True)


        xavier_usb_instance = instances.stdout.split("/")[5]

        return xavier_usb_instance


    def list_devices(self):
        number_devices = 0
        xavier_instances = []
        command = "lsusb"
        usb_devices = subprocess.run(command, capture_output= True, text=True, check = True)
        usb_devices = usb_devices.stdout.splitlines()

        for device in usb_devices:
            device = device.split(":",1)[1].strip()
            if device == self.xavier_id:
                number_devices = number_devices + 1
                xavier_instances.append(self.get_xavier_instances())

        if number_devices == 0:
            print("No Jetson Xavier connected")

            return number_devices

        else:  

            return number_devices, xavier_instances

# jetson = Jetson()

# number = jetson.list_devices()
# print(number)

#jetson.get_xavier_instances()