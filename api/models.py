from pydantic import BaseModel

class DestroyEnvVMRequest(BaseModel):
    vm_name: str
    macvlan_interface: str


class CreateUser(BaseModel):
    user_name: str
    user_network_id: int

    