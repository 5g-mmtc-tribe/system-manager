#-------------------------------------------------------------------------------------------------------------------
# Test the REST API
#-------------------------------------------------------------------------------------------------------------------

import requests
import json


#--------------------------------------------------------------------------------------------------------------------
## Get resource list
#--------------------------------------------------------------------------------------------------------------------

response = requests.post('http://127.0.0.1:8000/get_resource_list')
print(response.status_code)
print(response.content)


#--------------------------------------------------------------------------------------------------------------------
# Turn on all nodes
#--------------------------------------------------------------------------------------------------------------------


# response = requests.post('http://127.0.0.1:8000/turn_on_all')
# print(response.status_code)


#--------------------------------------------------------------------------------------------------------------------
# Turn off all nodes
#--------------------------------------------------------------------------------------------------------------------

response = requests.post('http://127.0.0.1:8000/testbed_reset')
print(response.status_code)
print(response.json())