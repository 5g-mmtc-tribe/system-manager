from dataclasses import dataclass


@dataclass
class UserEnv:
    interface_name: str 
    macvlan_name: str 
    ip_addr: str
    distribution: str 
    container_name: str
    ip_addr_veth: str 
    bridge: str
    interface_dhcp: str 