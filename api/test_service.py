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
    'user_name': "mehdi",
    'user_network_id': '90'
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


#-------------------------------------------------------------------------------------------------------------------
# Destroying user environment VM
#-------------------------------------------------------------------------------------------------------------------
data = {
    'vm_name': 'testvm',
    'macvlan_interface': 'macvlan_testvm'
}

response = requests.post('http://127.0.0.1:8000/destroy_env_vm', json=data)
print(response.status_code)
print(response.json())


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



# #-----------------------------------------------------------------------
# # Getting user info
# #-----------------------------------------------------------------------
data = {
    'user_name': "mehdi",
    'user_network_id': '90'
}

response_user_info = requests.post('http://127.0.0.1:8000/get_user_info', json=data)
print(response_user_info.status_code)
print(response_user_info.json())


#----------------------------------------------------
# Creating user env
#----------------------------------------------------

# # Convert JSON string to dictionary
# user_info_data = json.loads(response_user_info.json())

# data = {
#     'ubuntu_version': '24.04',
#     'vm_name': user_info_data[''],
#     'root_size': '4GiB',
#     'user_info': user_info_data
# }

# # Create Pydantic model instance
# request_data = CreateUserEnvVMRequest(**data)

# # Send request
# response = requests.post('http://127.0.0.1:8000/create_user_env_vm', json=request_data.dict())
# print(response.status_code)
# print(response.json())

#----------------------------------------------------
