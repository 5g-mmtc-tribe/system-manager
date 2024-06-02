import subprocess

class MacVlan:
    def __init__(self, interface_name):
        self.interface_name = interface_name


    def create_macvlan(self, macvlan_name):
        self.add_macvlan(macvlan_name)
        self.set_macvlan_up(macvlan_name)

    def add_macvlan(self, macvlan_name):
        try:
            command = ["sudo", "ip", "link", "add", macvlan_name, "link", self.interface_name, "type", "macvlan", "mode", "bridge"]
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError:
            print(f"Macvlan {macvlan_name} exists. Creation cannot be done.")

    def set_macvlan_up(self, macvlan_name):
        command = ["sudo", "ip", "link", "set", "dev", macvlan_name, "up"]
        subprocess.run(command, check=True)

    def macvlan_exists(self, macvlan_name):
        try:
            subprocess.check_output(["ip", "link", "show", macvlan_name], stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError:
            return False

    
    def set_ip_addr(self, ip_addr, macvlan_name):
        command = ["sudo", "ip", "addr",  "add", ip_addr ,"dev", macvlan_name]
        #print(command)
        subprocess.run(command, check=True)

    
    def delete_macvlan(self, macvlan_name):
        command = ["sudo", "ip", "link", "del", macvlan_name]
        subprocess.run(command, check=True)
        print("Macvlan destroyed")

# # Example usage
# interface_name = "enp2s0"
# macvlan = "macvlan1"
# ip_addr = "192.168.100.8/24"
# creator = MacVlan(interface_name)

# #creator.set_ip_addr(ip_addr, macvlan)

# result = creator.macvlan_exists("macrootfs")
# print(result)
# print(creator.add_macvlan("macrootfs"))
