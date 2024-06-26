import requests
import json
from models import CreateUserEnvVMRequest, UserNetworkInfo







#------------------------------------------------------------------------------------------------------------------
# Global variables: user_name and user_network_id
#------------------------------------------------------------------------------------------------------------------

data = {
    'user_name': "ferna",
    'user_network_id': '90'
}

#-------------------------------------------------------------------------------------------------------------------
## Creating new users
#-------------------------------------------------------------------------------------------------------------------
""""
response = requests.post('http://193.55.250.148:8083/create_user', json=data)
print(response.status_code)
print(response.json())
"""

# #-----------------------------------------------------------------------
# # Getting user info
# #-----------------------------------------------------------------------
data = {
    'user_name': "ferna",
    'user_network_id': '90'
}

response_user_info = requests.post('http://193.55.250.148:8083/get_user_info', json=data)
print(response_user_info.status_code)
print(response_user_info.json())
# Convert JSON string to dictionary
user_info_data = json.loads(response_user_info.json())

#-------------------------------------------------------------------------------------------------------------------
# Destroying user environment VM
#------------------------------------------------------------------------------------------------------------------

data = {
    'vm_name': user_info_data['user_name'],
    'macvlan_interface': user_info_data['macvlan_interface']
}

response = requests.post('http://193.55.250.148:8083/destroy_env_vm', json=data)
print(response.status_code)
print(response.json())
#----------------------------------------------------
# Creating user env
#----------------------------------------------------

"""user_env_info = {
    'ubuntu_version': '24.04',
   'vm_name': user_info_data['user_name'],
     'root_size': '40GiB',
     'user_info': user_info_data
 }

# # Create Pydantic model instance
request_data = CreateUserEnvVMRequest(**user_env_info)

# # Send request
response = requests.post('http://193.55.250.148:8083/create_user_env_vm', json=request_data.dict())
print(response.status_code)
print(response.json())"""
