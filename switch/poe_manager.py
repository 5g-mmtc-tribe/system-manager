from switch_manager import SwitchManager



# Define the device
device = {
 'device_type': 'cisco_ios_telnet',
 'ip': '192.168.0.30',
 'port':23,
 'password': 'tribe',
}


switch = SwitchManager(device_type = device['device_type'],
                            ip = device['ip'],
                            port = device['port'],
                            password = device['password'])



#out = switch_obj.sendCommand('show ip int bri')
#print(out)
# # # poe
interface = "GigabitEthernet 1/0/11"
# #interface = "GigabitEthernet 1/0/21"

switch.poe_off(interface)
#switch.poe_on(interface)

