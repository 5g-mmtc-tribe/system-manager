import requests
import json,os
from models import CreateUserEnvVMRequest, UserNetworkInfo

response = requests.post('http://193.55.250.148:8083/turn_on_all')
print(response.status_code)
print(response.json())

