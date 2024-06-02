#-------------------------------------------------------------------------------------------------------------------
# Test the REST API
#-------------------------------------------------------------------------------------------------------------------

import requests
import json

#--------------------------------------------------

#response = requests.post('http://127.0.0.1:8000/my_endpoint', data=json.dumps(data), headers=headers)
response = requests.post('http://127.0.0.1:8000/get_active_jetsons_list')
print(response.status_code)
print(response.content)

#--------------------------------------------------

response = requests.post('http://127.0.0.1:8000/get_resource_list')
print(response.status_code)
print(response.content)

#--------------------------------------------------

data = {'user': "no-user", "request": "nothing"}
#headers = {'Content-Type': 'application/json'}

response = requests.post('http://127.0.0.1:8000/create_env', json=data) #, headers=headers)
print(response.status_code)
print(response.content)

#-------------------------------------------------------------------------------------------------------------------
