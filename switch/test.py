from netmiko import Netmiko
import time



def sendCommandTiming(netCon, cmd):
    netCon.write_channel(cmd+'\n')
    time.sleep(0.1)
    out = netCon.read_channel()
    return out





def enable_device(net_con, enable_password):
    # Send the enable command
    out = sendCommandTiming(net_con, 'enable')

    # Check if the password prompt is detected
    if 'Password:' in out:
        # Write the enable password to the channel
        net_con.write_channel(enable_password + '\n')
        time.sleep(0.1)

    # Read the output after providing the password
    out += net_con.read_channel()
    return out


# Define the device
device = {
 'device_type': 'cisco_ios_telnet',
 'ip': '192.168.0.30',
 'port':23,
 'password': 'tribe',
}

# Initialize Netmiko connection
netCon = Netmiko(**device)

# Check if already in enable mode
print(netCon.check_enable_mode())


out = sendCommandTiming(netCon, 'show ip int bri')
#print(out)

print("Actual fun here")
#out = sendCommandTiming(netCon, 'enable')
#print(out)
print(enable_device(netCon, "tribe"))


print(netCon.check_enable_mode())

command = "disable"
sendCommandTiming(netCon, command)
print(netCon.check_enable_mode())
