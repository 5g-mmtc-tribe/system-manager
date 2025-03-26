from switch_manager import SwitchManager
import time
import os
import sys
import json

class PoeManager:

    def __init__(self, switch):
        self.switch = switch
    

    def turn_on(self,interface):
        self.switch.poe_on(interface)
        time.sleep(7)

    def turn_off(self,interface):
        self.switch.poe_off(interface)
        time.sleep(7)

    def get_switch_interfaces(self):

        interfaces = []
        # Get the absolute path of the parent directory
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
        # Now include the directory path in the file path
        file_path = os.path.join(script_path, 'resource.json')

        # Open and read the JSON file
        with open(file_path, 'r') as file:
            resources = json.load(file)

            for resource in resources:
                print(resource)
                interfaces.append(resource['switch_interface'])


        return interfaces

    def turn_all_off(self):

        interfaces = self.get_switch_interfaces()

        for interface in interfaces:
            print(interface)
            self.switch.poe_off(interface)
            time.sleep(7)
            
                
              



    def turn_all_on(self):

        interfaces = self.get_switch_interfaces()

        for interface in interfaces:
            print(interface)
            self.switch.poe_on(interface)
            time.sleep(7)



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




power = PoeManager(switch)
#switch.poe_on("GigabitEthernet1/0/14")
# switch_interfaces = power.get_switch_interfaces()
# print(switch_interfaces)

#power.turn_all_off()

# # #out = switch_obj.sendCommand('show ip int bri')
# # #print(out)
# # # # # poe
# # interface_1 = "GigabitEthernet 1/0/11"
# # interface_2 = "GigabitEthernet 1/0/13"
# # interfaces = [interface_1, interface_2]


# # def turn_all_off():
# #     for interface in interfaces:
# #         print(interface)
# #         switch.poe_off(interface)
# #         time.sleep(5)



# # def turn_all_on():
# #     for interface in interfaces:
# #         print(interface)
# #         switch.poe_on(interface)
# #         time.sleep(5)

# # switch.poe_off(interface_2)
# # #switch.poe_on(interface)

# # #turn_all_off()

# # #turn_all_on()

