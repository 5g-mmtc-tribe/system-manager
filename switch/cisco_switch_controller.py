from netmiko import ConnectHandler
import logging
from datetime import datetime


logging.basicConfig(filename='netmiko_global.log', level=logging.DEBUG)
logger = logging.getLogger("netmiko")

class SwitchManager():
    def __init__(self, device_type, ip, port, password):
        self.esw = {
            'device_type': device_type,
            'ip': ip,
            'port': port,
            'password': password,
            "session_log": 'netmiko_session.log'
        }

    def connect(self):
        try:
            net_connect = ConnectHandler(**self.esw)
            return net_connect
        except ConnectionRefusedError:
            print("Connection refused. Check Telnet service and configuration.")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def enable_switch(self):
        try:
            net_connect = self.connect()
            if net_connect:
                net_connect.enable()
                return net_connect
            else:
                return None
        except Exception as e:
            print(f"Error enabling switch: {e}")
            return None

    def execute_command(self, command):
        if self.connect() is not None:
            output = self.connect().send_command(command)
            self.connect().disconnect()
            return output
        else:
            return "Failed to execute command."

    

    

# Example usage

device_type='cisco_ios_telnet'
ip='192.168.0.30' 
port=23 
password='tribe'
switch_manager = SwitchManager(device_type, ip, port, password)
output = switch_manager.execute_command('show ip int brief')
print(output)
#print("trying 1")
#switch_manager.connect()

print("testing...")
#switch_manager.connect_enable()
net_connect = switch_manager.enable_switch()

