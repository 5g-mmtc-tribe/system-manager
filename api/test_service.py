#-------------------------------------------------------------------------------------------------------------------
# Test the REST API
#-------------------------------------------------------------------------------------------------------------------

import requests
import json
from models import CreateUserEnvVMRequest, UserNetworkInfo



#--------------------------------------------------

## Get resource list

response = requests.post('http://127.0.0.1:8000/get_resource_list')
print(response.status_code)
print(response.content)

# #-------------------------------------------------


## Creating new users

data = {
    'user_name': "fernando",
    'user_network_id': '7'
}

response = requests.post('http://127.0.0.1:8000/create_user', json=data)
print(response.status_code)
print(response.json())

#-------------------------------------------------------------------------------------------------------------------
## Clearing active users


# response = requests.post('http://127.0.0.1:8000/clear_active_users', json=data)
# print(response.status_code)
# print(response.json())

#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------



# Destroying user environment VM

# data = {
#     'vm_name': 'testvm',
#     'macvlan_interface': 'macvlan_testvm'
# }

# response = requests.post('http://127.0.0.1:8000/destroy_env_vm', json=data)
# print(response.status_code)
# print(response.json())


# -------------------------------------
# Turn on all nodes

# response = requests.post('http://127.0.0.1:8000/turn_on_all')
# print(response.status_code)
# print(response.json())

# -------------------------------------


# Turn off all nodes

# response = requests.post('http://127.0.0.1:8000/testbed_reset')
# print(response.status_code)
# print(response.json())


#----------------------------------------------------
# Creating user env
#----------------------------------------------------

data = {
    'ubuntu_version': '24.04',
    'vm_name': 'testvm',
    'root_size': '4GiB',
    'user_info': {
        'user_name': 'testvm',
        'user_network_id': 75,
        'user_subnet': '192.168.75.0/24',
        'nfs_ip_addr': '192.168.75.1/24',
        'macvlan_interface': 'macvlan_testvm',
        'macvlan_ip_addr': '192.168.75.2/24'
    }
}

# Create Pydantic model instance
request_data = CreateUserEnvVMRequest(**data)

# Send request
response = requests.post('http://127.0.0.1:8000/create_user_env_vm', json=request_data.dict())
print(response.status_code)
print(response.json())