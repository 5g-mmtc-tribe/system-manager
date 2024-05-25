import subprocess

class Jetson:

    def list_devices(self):
        command = "lsusb"
        usb_devices = subprocess.run(command, capture_output= True, text=True, check = True)
        print(usb_devices.stdout)




jetson = Jetson()

jetson.list_devices()
