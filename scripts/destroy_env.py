from scripts.macvlan import MacVlan
from scripts.container_create import Container
from scripts.user_env import UserEnv



def destroy_user_env(config: UserEnv):
    interface_name = config.interface_name
    
    macvlan_name = config.macvlan_name
    ip_addr = config.ip_addr


    # container
    distribution = config.distribution
    container_name = config.container_name
    ip_addr_veth = config.ip_addr_veth

    print("Attempting to delete container...")
    container = Container(distribution, container_name)
    container.delete_container(container_name)
    print("Container deleted successfully!")
    
    print("Attempt to destroy macvlan")
    
    macvlan = MacVlan(interface_name, macvlan_name)

    macvlan.delete_macvlan(macvlan_name)

    

# if __name__=="__main__":
#     config = UserEnv(
#         interface_name='enp2s0',
#         macvlan_name='demomacvlan1',
#         ip_addr='192.168.100.9/24',
#         distribution='ubuntu:22.04',
#         container_name='finalTest',
#         ip_addr_veth='192.168.100.30/24',
#         bridge='lxdbr0',
#         interface_dhcp='eth1'
#     )
    
#     main(config)