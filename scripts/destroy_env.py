from macvlan import MacVlan



def main():
    interface_name = "enp2s0"
    #interface_name = "enx3c18a0b38076"

    macvlan_name = "demomacvlan1"
    ip_addr = "192.168.100.9/24"


    # container
    distribution = 'ubuntu:22.04'
    container_name = 'demo'
    ip_addr_veth = "192.168.100.30/24"

    print("Attempt to destroy macvlan")
    
    macvlan = MacVlan(interface_name, macvlan_name)

    macvlan.delete_macvlan(macvlan_name)



if __name__=="__main__":
    main()