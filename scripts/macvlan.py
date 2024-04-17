import subprocess

class MacVlan:

    def __init__(self):
        pass


    def create_macvlan(self, interface_name, parent_interface, macvlan_name):

        subprocess.run(["sudo", "ip", "link", "add", parent_interface, macvlan_name, "type", "macvlan"], check = True)
        subprocess.run(["sudo", "ip", "link", "set", "dev", macvlan_name, "up"], check=True)




# Example usage
creator = MacVlan()
creator.create_macvlan("enp2s0", "macvlan1")
