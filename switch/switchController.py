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
        sendCommand(netCon, conf_t)
        sendCommand(netCon, "interface " +interface)
        power_off = "power inline never"
        sendCommand(netCon, power_off)
        sendCommand(netCon, "end")


    def poe_on(self, netCon, interface):
        conf_t = "conf t"
        sendCommand(netCon, conf_t)
        #sendCommand(netCon, interface)
        sendCommand(netCon, "interface " +interface)

        power_on = "power inline auto"
        sendCommand(netCon, power_on)
        sendCommand(netCon, "end")







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


# print(netCon.check_enable_mode())
# enable_device(netCon, "tribe")
# print(netCon.check_enable_mode())


# #interface = "GigabitEthernet 1/0/16"
# interface = "GigabitEthernet 1/0/21"


# print("Turning on 1")
# poe_on(netCon, interface)
# time.sleep(20)
# print("turning off 2")
# poe_off(netCon, interface)
# time.sleep(20)
# print("turning on 3")
# poe_on(netCon, interface)
# time.sleep(20)
# print("final turning off")
# poe_off(netCon, interface)
# # poe


# print(netCon.check_enable_mode())
# enable_device(netCon, "tribe")
# print(netCon.check_enable_mode())



# print("Turning on 1")
# poe_on(netCon, interface)
# time.sleep(20)
# print("turning off 2")
# poe_off(netCon, interface)
# time.sleep(20)
# print("turning on 3")
# poe_on(netCon, interface)
# time.sleep(20)
# print("final turning off")
# poe_off(netCon, interface)
# # poe


# print(netCon.check_enable_mode())
# enable_device(netCon, "tribe")
# print(netCon.check_enable_mode())


# #interface = "GigabitEthernet 1/0/16"
# interface = "GigabitEthernet 1/0/21"


# print("Turning on 1")
# poe_on(netCon, interface)
# time.sleep(20)
# print("turning off 2")
# poe_off(netCon, interface)
# time.sleep(20)
# print("turning on 3")
# poe_on(netCon, interface)
# time.sleep(20)
# print("final turning off")
# poe_off(netCon, interface)