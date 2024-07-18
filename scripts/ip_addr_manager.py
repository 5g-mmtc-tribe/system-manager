import os 
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
        prefix_parts[-1] = '1'
        
        # Reassemble the IP address and subnet mask
        macvlan_interface_ip = f"{'.'.join(prefix_parts)}/{prefix[1]}"
        return macvlan_interface_ip

    def jetson_ip(self , nfs_ip_addr):
        
        # Split the subnet into its components
        prefix = nfs_ip_addr.split('/')
        prefix_parts = prefix[0].split('.')
        
        # Change the last part of the IP address to '20'
        prefix_parts[-1] = '20'
        
        # Reassemble the IP address and subnet mask
        jetson_ip = f"{'.'.join(prefix_parts)}"
        print("jetson_ip",jetson_ip)
        return jetson_ip 
    
    def update_network_config(self,file_path, new_ip):
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            return

        # Read the file content
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Modify the IP address in the file
        for i, line in enumerate(lines):
            if "addresses:" in line:
                next_line_index = i + 1
                if next_line_index < len(lines):
                    lines[next_line_index] = f"              - {new_ip}\n"

        # Write the modified content back to the file
        with open(file_path, 'w') as file:
            file.writelines(lines)

        print(F"File '{file_path}' has been updated with the new IP address: {new_ip}")
    def update_dhcp_configuration(self ,file_path, nfs_ip):
            # Generate the new content for the DHCP configuration
            new_content = f"""\
        subnet 192.168.0.0 netmask 255.255.255.0 {{
            range {nfs_ip.rsplit('.', 1)[0]}.12 {nfs_ip.rsplit('.', 1)[0]}.15;
            option routers {nfs_ip};
            option domain-name-servers 8.8.8.8, 8.8.4.4;
        }}
        """

            # Remove existing file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted existing file: {file_path}")

            # Write the new content to the file
            with open(file_path, 'w') as file:
                file.write(new_content)

            print(f"Created new DHCP configuration file: {file_path}")
        
#ip = IpAddr()
# subnet = ip.user_subnet(4)
# print(subnet)
# print(ip.nfs_interface_ip(6))
# print(ip.macvlan_interface_ip(5))
#ip.update_dhcp_configuration("/home/mehdi/system-manager/api/dhcpConfig.txt","192.168.180.0/24")