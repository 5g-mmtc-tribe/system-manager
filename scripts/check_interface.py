import subprocess

def check_interface_exists(interface):
    """Check if the given interface exists."""
    try:
        subprocess.check_output(["ip", "link", "show", interface])
        return True
    except subprocess.CalledProcessError:
        return False

def check_interface_up(interface):
    """Check if the given interface is up."""
    try:
        output = subprocess.check_output(["ip", "link", "show", interface]).decode('utf-8')
        return 'UP' in output
    except subprocess.CalledProcessError:
        return False

# Example usage
interface = "enx3c18a0b38076" # Replace with your interface name
if check_interface_exists(interface):
    if check_interface_up(interface):
        print(f"Interface {interface} exists and is up.")
    else:
        print(f"Interface {interface} exists but is not up.")
else:
    print(f"Interface {interface} does not exist.")

