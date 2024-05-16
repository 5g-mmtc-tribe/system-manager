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

    def enable_device(self):
        # Send the enable command
        out = self.sendCommand('enable')

        # Check if the password prompt is detected
        if 'Password:' in out:
            # Write the enable password to the channel
            self.netCon.write_channel(self.esw['password'] + '\n')
            time.sleep(0.1)

        # Read the output after providing the password
        out += self.netCon.read_channel()
        return out

    def poe_off(self, interface):

        if not self.checker():
            print("Device is not in enable mode. Enabling...")
            self.enable_device()

        conf_t = "conf t"
        self.sendCommand(conf_t)
        self.sendCommand("interface " +interface)
        power_off = "power inline never"
        self.sendCommand(power_off)
        # power_disable = "no power inline"
        # self.sendCommand(power_disable)
        self.sendCommand("end")


    def poe_on(self, interface):
        if not self.checker():
            print("Device is not in enable mode. Enabling...")
            self.enable_device()

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


print(switch_obj.enable_device())
print(switch_obj.checker())


command = "disable"
out = switch_obj.sendCommand(command)
print(switch_obj.checker())



# # poe
interface = "GigabitEthernet 1/0/16"
#interface = "GigabitEthernet 1/0/21"

switch_obj.poe_on(interface)



time.sleep(30)

switch_obj.poe_off(interface)

time.sleep(30)

switch_obj.poe_on(interface)


time.sleep(30)

switch_obj.poe_off(interface)
