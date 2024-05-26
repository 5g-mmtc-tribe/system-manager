class IpAddr:

    def __init__(self):
        pass

    def user_subnet(self, user_number):
        subnet = f"192.168.{user_number}.0/24"
        return subnet

    def nfs_interface(self, user_number):
        user_subnet = self.user_subnet(user_number)
        print(user_subnet)
        
        # Split the subnet into its components
        prefix = user_subnet.split('/')
        prefix_parts = prefix[0].split('.')
        
        # Change the last part of the IP address to '1'
        prefix_parts[-1] = '1'
        
        # Reassemble the IP address and subnet mask
        nfs_interface = f"{'.'.join(prefix_parts)}/{prefix[1]}"
        return nfs_interface



ip = IpAddr()
subnet = ip.user_subnet(4)
print(subnet)
print(ip.nfs_interface(6))