import sys, os

import system_manager_api as sm

# Get the absolute path of the parent directory
script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts'))
sys.path.append(script_path)
# Now import the function from the script
from user_env import UserEnv



def main():

    config = UserEnv(
        interface_name='enp2s0',
        macvlan_name='demomacvlan1',
        ip_addr='192.168.100.9/24',
        distribution='ubuntu:22.04',
        container_name='finalTest',
        ip_addr_veth='192.168.100.30/24',
        bridge='lxdbr0',
        interface_dhcp='eth1'
    )

    #create_env(config)
    #destroy_env(config)

    

    # jetsons = sm.get_resource_list()
    # print(jetsons)

    sm.allocate_active_users("cedric", 75)
    sm.allocate_active_users("user_test", 76)
    sm.testbed_reset()
        #turn_on_all_nodes()
        #clear_active_users()

if __name__=="__main__":
    main()