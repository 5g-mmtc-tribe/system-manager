#-------------------------------------------------------------------------------------------------------------------
# Test the REST API
#-------------------------------------------------------------------------------------------------------------------

import requests
import json



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


# Destroying user environment VM

# data = {
#     'vm_name': 'testvm',
#     'macvlan_interface': 'macvlan_testvm'
# }

# response = requests.post('http://127.0.0.1:8000/destroy_env_vm', json=data)
# print(response.status_code)
# print(response.json())