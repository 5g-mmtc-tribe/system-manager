from dataclasses import dataclass


@dataclass
class UserEnv:
    interface_name: str = 'enp2s0'
    macvlan_name: str = 'demomacvlan1'
    ip_addr: str = '192.168.100.9/24'
    distribution: str = 'ubuntu:22.04'
    container_name: str = 'demo'
    ip_addr_veth: str = '192.168.100.30/24'
    bridge: str = 'lxdbr0'
    interface_dhcp: str = 'eth1'