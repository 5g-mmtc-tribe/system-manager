from pydantic import BaseModel

class jetsonInfo(BaseModel):
    nfs_ip_addr: str
    nfs_path:str
    usb_instance :str

class DestroyEnvVMRequest(BaseModel):
    vm_name: str
    macvlan_interface: str


class CreateUser(BaseModel):
    user_name: str
    user_network_id: int


class UserNetworkInfo(BaseModel):
    user_name: str
    user_network_id: int
    user_subnet: str
    nfs_ip_addr: str
    macvlan_interface: str
    macvlan_ip_addr: str
    vlan_ip_addr :str

class CreateUserEnvVMRequest(BaseModel):
    ubuntu_version: str 
    vm_name: str
    root_size: str
    user_info: UserNetworkInfo

class TurnNode(BaseModel):
    node_name :str