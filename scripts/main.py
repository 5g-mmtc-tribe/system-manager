import subprocess
from network_interface import NetworkInterface
from macvlan import MacVlan
from container_create import Container
from user_env import UserEnv
import argparse


def attatch_macvlan_container(macvlan_name, container_name, container_veth):
    command = ["sudo", "lxc", "network", "attach", macvlan_name, container_name, container_veth]
    subprocess.run(command, check=True)

def attach_container_bridge(container_name, interface_name, bridge):
    command = ["sudo", "lxc", "config", "device", "add", container_name, interface_name, "nic", "nictype=bridged", "parent=" + bridge]
    subprocess.run(command, check=True)

def dhcp(container_name, interface_dhcp):
    command = ["sudo", "lxc", "exec", container_name, "--", "dhclient", interface_dhcp]
    subprocess.run(command, check=True)



def main(config: UserEnv):
    interface = NetworkInterface(config.interface_name)
    if interface.check_interface_exists():
        if interface.check_interface_up():
            print(f"Interface {config.interface_name} exists and is up.")
            macvlan = MacVlan(config.interface_name, config.macvlan_name)
            if not macvlan.macvlan_exists():
                print(f"Creating macvlan {config.macvlan_name} for interface {config.interface_name}.")
                macvlan.create_macvlan()
                print(f"Macvlan {config.macvlan_name} created.")
            else:
                print(f"Macvlan {config.macvlan_name} already exists.")
        else:
            print(f"Interface {config.interface_name} exists but is not up.")
    else:
        print(f"Interface {config.interface_name} does not exist.")

    macvlan.set_ip_addr(config.ip_addr, config.macvlan_name)
    print("IP address attributed")

    print("Macvlan created successfully, now creating container")
    container = Container(config.distribution, config.container_name)

    try:
        container.start_container(config.distribution, config.container_name)
        print("Container started successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error starting container: {e}")
        return

    try:
        container_veth = container.get_network_interfaces(config.container_name)[0]
        print(f"Attempt to attach macvlan to container {config.container_name} with veth {container_veth}")
        attatch_macvlan_container(config.macvlan_name, config.container_name, container_veth)
        print("Attachment successful")
    except subprocess.CalledProcessError as e:
        print(f"Error attaching macvlan to container: {e}")
        return

    try:
        container.assign_ip_address(config.container_name, container_veth, config.ip_addr_veth)
        print("IP address assignment to veth successful")
    except subprocess.CalledProcessError as e:
        print(f"Error assigning IP address to veth: {e}")
        return

    try:
        attach_container_bridge(config.container_name, config.interface_dhcp, config.bridge)
        print("Container connected to the bridge")
    except subprocess.CalledProcessError as e:
        print(f"Error connecting container to bridge: {e}")
        return

    try:
        dhcp(config.container_name, config.interface_dhcp)
        print("DHCP request successful, container ready for use!")
    except subprocess.CalledProcessError as e:
        print(f"Error during DHCP request: {e}")

if __name__ == "__main__":
    config = UserEnv(
        interface_name='enp2s0',
        macvlan_name='demomacvlan1',
        ip_addr='192.168.100.9/24',
        distribution='ubuntu:22.04',
        container_name='demo',
        ip_addr_veth='192.168.100.30/24',
        bridge='lxdbr0',
        interface_dhcp='eth1'
    )
    main(config)
