import subprocess

class MacVlan:
    def __init__(self, interface_name, macvlan_name):
        self.interface_name = interface_name
        self.macvlan_name = macvlan_name

    def create_macvlan(self):
        self.add_macvlan()
        self.set_macvlan_up()

    def add_macvlan(self):
        try:
            command = ["sudo", "ip", "link", "add", self.macvlan_name, "link", self.interface_name, "type", "macvlan", "mode", "bridge"]
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError:
            print(f"Macvlan {self.macvlan_name} exists. Creation cannot be done.")

    def set_macvlan_up(self):
        command = ["sudo", "ip", "link", "set", "dev", self.macvlan_name, "up"]
        subprocess.run(command, check=True)

    def macvlan_exists(self):
        try:
            subprocess.check_output(["ip", "link", "show", self.macvlan_name], stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError:
            return False

# # Example usage
# interface_name = "enp2s0"
# macvlan = "macvlan1"
# creator = MacVlan(interface_name, macvlan)
# creator.create_macvlan()
