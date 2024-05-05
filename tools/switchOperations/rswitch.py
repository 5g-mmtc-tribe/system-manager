from netmiko import ConnectHandler

# Define the device
esw = {
 'device_type': 'cisco_ios_telnet',
 'ip': '192.168.0.30',
 'port':23,
 'password': 'tribe',
}
# Establish a connection to the ESW
try:
    net_connect = ConnectHandler(**esw)

    # Execute a command
    output = net_connect.send_command('show ip int brief')

    # Print the output
    print(output)

    # Disconnect from the ESW
    net_connect.disconnect()

except ConnectionRefusedError:
    print("Connection refused. Check Telnet service and configuration.")
except Exception as e:
    print(f"Error: {e}")
