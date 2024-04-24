import subprocess
from network_interface import NetworkInterface
from macvlan import MacVlan
from container_create import Container

def main():


    interface_name = "enp2s0"
    #interface_name = "enx3c18a0b38076"

    macvlan_name = "macvlan1"
    ip_addr = "192.168.100.9/24"

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

    distribution = 'ubuntu:22.04'
    container_name = 'testcontainers'

    container = Container(distribution, container_name)

    container.start_container(distribution,container_name)
    print("container started successfully")
    container.delete_container(container_name)
    print("container deleted")


if __name__== "__main__":
    main()