import subprocess

def create_macvlan(interface_name, parent_interface, macvlan_name):
    # Create the macvlan interface
    subprocess.run(["sudo", "ip", "link", "add", "link", parent_interface, macvlan_name, "type", "macvlan"], check=True)
    
    # Bring the macvlan interface up
    subprocess.run(["sudo", "ip", "link", "set", "dev", macvlan_name, "up"], check=True)
    
    # Assign an IP address to the macvlan interface (optional)
    # subprocess.run(["sudo", "ip", "addr", "add", "192.168.1.20/24", "dev", macvlan_name], check=True)

# Example usage
create_macvlan("eth0", "m0")

