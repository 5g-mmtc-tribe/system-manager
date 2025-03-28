from pydantic import BaseModel
from typing import Deque, List, Optional, Tuple
class sshInfo(BaseModel):
    user_name :str
class jetsonInfo(BaseModel):
    nfs_ip_addr: str
    nfs_path:str
    usb_instance :str
    switch_interface:str
    model:str
    nvidia_id:str

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


class CreateUserEnvVMRequest(BaseModel):
    ubuntu_version: str 
    vm_name: str
    root_size: str
    user_info: UserNetworkInfo
    nodes:Optional[list] = None

class TurnNode(BaseModel):
    node_name :str

class VlanNode(BaseModel):
    node_name :str
    vlan_id :int

class Ressource(BaseModel):
    name :str