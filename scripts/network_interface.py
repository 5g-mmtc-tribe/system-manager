import subprocess

class NetworkInterface:
    def __init__(self, interface_name):
        self.interface_name = interface_name

    def check_interface_exists(self):
        """Check if the given interface exists."""
        try:
            subprocess.check_output(["ip", "link", "show", self.interface_name])
            return True
        except subprocess.CalledProcessError:
            return False

    def check_interface_up(self):
        """Check if the given interface is up."""
        try:
            output = subprocess.check_output(["ip", "link", "show", self.interface_name]).decode('utf-8')
            return 'UP' in output
        except subprocess.CalledProcessError:
            return False

# Example usage

interface_name = "enp2s0"
#interface_name = "enx3c18a0b38076"
interface = NetworkInterface(interface_name) # Replace with your interface name
if interface.check_interface_exists():
    if interface.check_interface_up():
        print(f"Interface {interface.interface_name} exists and is up.")
    else:
        print(f"Interface {interface.interface_name} exists but is not up.")
else:
    print(f"Interface {interface.interface_name} does not exist.")