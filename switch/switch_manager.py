from netmiko import Netmiko
import time

class SwitchManager():

    def __init__(self, device_type, ip, port, password ,username=None, enable_password=None):
        
        self.esw = {
            'device_type': device_type,
            'ip': ip,
            'port': port,
            'password': password ,
            'username': username,# For SSH
            'secret': enable_password  # For enab
        }
        self.netCon = Netmiko(**self.esw)



    def check_enable_mode(self):
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


    def configure_vlan(self, vlan_id, vlan_name):
        if not self.check_enable_mode():
            self.enable_device()

        conf_t = "configure terminal"
        self.sendCommand(conf_t)
        self.sendCommand("vlan " + str(vlan_id))
        self.sendCommand("name "+ vlan_name)
        self.sendCommand("end")

    def poe_off(self, interface):

        if not self.check_enable_mode():
            self.enable_device()

        conf_t = "configure terminal"
        self.sendCommand(conf_t)
        self.sendCommand("interface " +interface)
        power_off = "power inline never"
        self.sendCommand(power_off)
        self.sendCommand("end")


    def poe_on(self, interface):
        if not self.check_enable_mode():
            self.enable_device()

        conf_t = "configure terminal"
        self.sendCommand(conf_t)
        self.sendCommand("interface " +interface)
        power_on = "power inline auto"
        self.sendCommand(power_on)
        self.sendCommand("end")

    def mode_access(self ,interface):
        if not self.check_enable_mode():
                self.enable_device()
        conf_t = "configure terminal"
        self.sendCommand(conf_t)
        self.sendCommand("interface " +interface)
        mode_access = "switchport mode access"
        self.sendCommand(mode_access)
        self.sendCommand("end")
    
    def vlan_access(self, interface, vlan_id):
        # Check if in enable mode, if not, enter it
        if not self.check_enable_mode():
            self.enable_device()

        # Create the commands to configure the interface
        config_commands = [
            f"interface {interface}",
            "switchport mode access",
            f"switchport access vlan {vlan_id}"
        ]

        # Sending the commands in configuration mode
        self.sendCommand('configure terminal')
        for cmd in config_commands:
            self.sendCommand(cmd)

        # Exit config mode
        self.sendCommand('end')





# Example usage:

#device_telnet = {
#    'device_type': 'cisco_ios_telnet',  # Telnet connection
#    'ip': '192.168.0.30',
#    'port': 23,
#    'password': 'tribe',
#    'username': None,  # Not needed for Telnet
#    'secret': 'enable_password'  # Enable password
#}
#switch_obj = SwitchManager(device_type=device_telnet['device_type'],
#                           ip=device_telnet['ip'],
#                           port=device_telnet['port'],
#                           password=device_telnet['password'],
#                           username=device_telnet['username'],
#                           enable_password=device_telnet['secret'])
# out = switch_obj.sendCommand('show ip int bri')
"""device_ssh = {
    'device_type': 'cisco_ios_ssh',  # SSH connection
    'ip': '192.168.0.30',
    'port': 22,
    'password': 'tribe',
    'username': 'tribe',  # Required for SSH
    'secret': 'tribe'  # Enable password
}
switch_obj = SwitchManager(device_type=device_ssh['device_type'],
                           ip=device_ssh['ip'],
                           port=device_ssh['port'],
                           password=device_ssh['password'],
                           username=device_ssh['username'],
                           enable_password=device_ssh['secret'])"""

# print(out)

# print(switch_obj.check_enable_mode())


# print(switch_obj.enable_device())
# print(switch_obj.check_enable_mode())


# command = "disable"
# out = switch_obj.sendCommand(command)
# print(switch_obj.check_enable_mode())


# vlan_id = 30
# vlan_name = "testing"
# switch_obj.configure_vlan(vlan_id,vlan_name)

# # # # poe
# # interface = "GigabitEthernet 1/0/16"
# # #interface = "GigabitEthernet 1/0/21"

# # switch_obj.poe_on(interface)



# # time.sleep(30)

# # switch_obj.poe_off(interface)

# # time.sleep(30)

# # switch_obj.poe_on(interface)


# # time.sleep(30)

# # switch_obj.poe_off(interface)
# old version
"""device = {
 'device_type': 'cisco_ios_telnet',
  'ip': '192.168.0.30',
  'port':23,
  'password': 'tribe',
 }


switch_obj = SwitchManager(device_type = device['device_type'],
                             ip = device['ip'],
                             port = device['port'],
                             password = device['password'])"""