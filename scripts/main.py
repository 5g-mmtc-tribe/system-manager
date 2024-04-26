import subprocess
from network_interface import NetworkInterface
from macvlan import MacVlan
from container_create import Container


def attatch_macvlan_container(macvlan_name, container_name, container_veth):

    command = ["sudo", "lxc", "network", "attach", macvlan_name, container_name, container_veth]
    subprocess.run(command, check = True)


def attach_container_bridge(container_name, interface_name, bridge):
    command = ["sudo", "lxc", "config", "device", "add" ,container_name, interface_name, "nic", "nictype=bridged", "parent="+ bridge]
    subprocess.run(command, check= True)

def dhcp(container_name, interface_dhcp):
    command = ["sudo", "lxc", "exec", container_name,  "--" ,"dhclient", interface_dhcp]
    subprocess.run(command, check= True)

def main():


    interface_name = "enp2s0"
    #interface_name = "enx3c18a0b38076"

    macvlan_name = "demomacvlan1"
    ip_addr = "192.168.100.9/24"


    # container
    distribution = 'ubuntu:22.04'
    container_name = 'demo'
    ip_addr_veth = "192.168.100.30/24"

    interface = NetworkInterface(interface_name) 
    if interface.check_interface_exists():
        if interface.check_interface_up():
            print(f"Interface {interface.interface_name} exists and is up.")
            # Check if the macvlan exists
            macvlan = MacVlan(interface_name, macvlan_name)
            if not macvlan.macvlan_exists():
                print(f"Creating macvlan {macvlan_name} for interface {interface_name}.")
                macvlan.create_macvlan()
                print(f"Macvlan {macvlan_name} created.")
            else:
                print(f"Macvlan {macvlan_name} already exists.")
        else:
            print(f"Interface {interface.interface_name} exists but is not up.")
    else:
        print(f"Interface {interface.interface_name} does not exist.")


    # IP address allocation
    macvlan.set_ip_addr(ip_addr, macvlan_name)
    print("ip address attributed")

    print("macvlan created successfully, now creating container")

    

    container = Container(distribution, container_name)

    container.start_container(distribution,container_name)
    print("container started successfully")
    #container.delete_container(container_name)
    #print("container deleted")

    print("Attempt to attach macvlan to container")
    container_veth = container.get_network_interfaces(container_name)[0]
    print(f"the container_veth is {container_veth}")
    print("Attaching macvlan to container")
    attatch_macvlan_container(macvlan_name, container_name, container_veth)
    print("Attachment successful")


    print("assignment of ip address to veth of container")
    container.assign_ip_address(container_name, container_veth, ip_addr_veth)
    print("Assignment successful")

    print("Connecting the container to the bridge")
    bridge = "lxdbr0"
    interface_dhcp = "eth1"
    attach_container_bridge(container_name, interface_dhcp, bridge)

    print("dhcp request...")    
    dhcp(container_name, interface_dhcp)
    print("container ready for use!")


if __name__== "__main__":
    main()