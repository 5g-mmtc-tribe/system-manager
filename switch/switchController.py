from netmiko import Netmiko
import time


class SwitchManager():

    def __init__(self, device_type, ip, port, password):
        
        self.esw = {
            'device_type': device_type,
            'ip': ip,
            'port': port,
            'password': password
        }
        self.netCon = Netmiko(**self.esw)



    def checker(self):
        return self.netCon.check_enable_mode()


    def sendCommand(self, cmd):
        self.netCon.write_channel(cmd+'\n')
        time.sleep(0.1)
        out = self.netCon.read_channel()
        return out

    def enable_device(self, enable_password):
        # Send the enable command
        out = self.sendCommand('enable')

        # Check if the password prompt is detected
        if 'Password:' in out:
            # Write the enable password to the channel
            self.netCon.write_channel(enable_password + '\n')
            time.sleep(0.1)

        # Read the output after providing the password
        out += self.netCon.read_channel()
        return out

    def poe_off(self, interface):
        conf_t = "conf t"
        self.sendCommand(conf_t)
        self.sendCommand("interface " +interface)
        power_off = "power inline never"
        self.sendCommand(power_off)
        # power_disable = "no power inline"
        # self.sendCommand(power_disable)
        self.sendCommand("end")


    def poe_on(self, interface):
        conf_t = "conf t"
        self.sendCommand(conf_t)
        self.sendCommand("interface " +interface)
        power_on = "power inline auto"
        self.sendCommand(power_on)
        self.sendCommand("end")

   






# Define the device
device = {
 'device_type': 'cisco_ios_telnet',
 'ip': '192.168.0.30',
 'port':23,
 'password': 'tribe',
}


switch_obj = SwitchManager(device_type = device['device_type'],
                            ip = device['ip'],
                            port = device['port'],
                            password = device['password'])

# Initialize Netmiko connection

# Check if already in enable mode


out = switch_obj.sendCommand('show ip int bri')
print(out)


print(switch_obj.checker())
print("Actual fun here")
# #out = sendCommand(netCon, 'enable')
# # #print(out)
# # print(enable_device("tribe"))
print(switch_obj.enable_device(device['password']))
print(switch_obj.checker())


command = "disable"
out = switch_obj.sendCommand(command)
print(switch_obj.checker())


# # poe
# #interface = "GigabitEthernet 1/0/16"
interface = "GigabitEthernet 1/0/21"

# Check if already in enable mode
if not switch_obj.checker():
    print("Device is not in enable mode. Enabling...")
    switch_obj.enable_device('tribe')

# Check if the device is enabled
if switch_obj.checker():
    print("Device is enabled. Proceeding with PoE commands...")
    print("Powering off PoE on interface", interface)
    switch_obj.poe_off(interface)
else:
    print("Device is not enabled. Unable to proceed with PoE commands.")


print("now we will wait a bit")
time.sleep(30)
print("turning on device now")
# Check if already in enable mode
if not switch_obj.checker():
    print("Device is not in enable mode. Enabling...")
    switch_obj.enable_device('tribe')

# Check if the device is enabled
if switch_obj.checker():
    print("Device is enabled. Proceeding with PoE commands...")
    print("Powering on PoE on interface", interface)
    switch_obj.poe_on(interface)
else:
    print("Device is not enabled. Unable to proceed with PoE commands.")
