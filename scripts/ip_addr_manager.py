class IpAddr:

    def __init__(self):
        pass

    def user_subnet(self, user_id):
        subnet = f"192.168.{user_id}.0/24"
        return subnet

    def nfs_interface_ip(self, user_id):
        user_subnet = self.user_subnet(user_id)
        print(user_subnet)
        
        # Split the subnet into its components
        prefix = user_subnet.split('/')
        prefix_parts = prefix[0].split('.')
        
        # Change the last part of the IP address to '1'
        prefix_parts[-1] = '1'
        
        # Reassemble the IP address and subnet mask
        nfs_interface = f"{'.'.join(prefix_parts)}/{prefix[1]}"
        return nfs_interface

    def macvlan_interface_ip(self, user_id):
        user_subnet = self.user_subnet(user_id)
        print(user_subnet)
        
        # Split the subnet into its components
        prefix = user_subnet.split('/')
        prefix_parts = prefix[0].split('.')
        
        # Change the last part of the IP address to '1'
        prefix_parts[-1] = '2'
        
        # Reassemble the IP address and subnet mask
        macvlan_interface_ip = f"{'.'.join(prefix_parts)}/{prefix[1]}"
        return macvlan_interface_ip




# ip = IpAddr()
# subnet = ip.user_subnet(4)
# print(subnet)
# print(ip.nfs_interface_ip(6))
# print(ip.macvlan_interface_ip(5))