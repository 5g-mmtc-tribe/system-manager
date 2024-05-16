from switchManager import SwitchManager



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




# # # poe
# interface = "GigabitEthernet 1/0/16"
# #interface = "GigabitEthernet 1/0/21"

# switch_obj.poe_on(interface)

