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


        print(instances.stdout)



    def list_devices(self):
        number_devices = 0
        command = "lsusb"
        usb_devices = subprocess.run(command, capture_output= True, text=True, check = True)
        usb_devices = usb_devices.stdout.splitlines()

        for device in usb_devices:
            device = device.split(":",1)[1].strip()
            if device == self.xavier_id:
                number_devices = number_devices + 1

        return number_devices

jetson = Jetson()

number = jetson.list_devices()
print(number)

jetson.get_xavier_instances()