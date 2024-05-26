#from user_env import UserEnv


import system_manager_api as sm
def main():

    # config = UserEnv(
    #     interface_name='enp2s0',
    #     macvlan_name='demomacvlan1',
    #     ip_addr='192.168.100.9/24',
    #     distribution='ubuntu:22.04',
    #     container_name='finalTest',
    #     ip_addr_veth='192.168.100.30/24',
    #     bridge='lxdbr0',
    #     interface_dhcp='eth1'
    # )

    #create_env(config)
    #destroy_env(config)

    sm.get_active_jetsons_list()
    


if __name__=="__main__":
    main()