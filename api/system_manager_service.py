#-------------------------------------------------------------------------------------------------------------------
# Define the REST API and run with FastAPI,uvicorn
#-------------------------------------------------------------------------------------------------------------------

from fastapi import FastAPI, Request, HTTPException
import system_manager_api 
import logging
import uvicorn
from pydantic import BaseModel
from models import DestroyEnvVMRequest, CreateUser,  CreateUserEnvVMRequest


logging.basicConfig(level=logging.ERROR)
app = FastAPI()

#--------------------------------------------------
# Get resource list
#--------------------------------------------------
@app.post('/get_resource_list')
def call_get_resource_list():
    try:
        resource_list = system_manager_api.get_resource_list()
        return resource_list
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail='Failed to get resource list')

#--------------------------------------------------
# Destroy user env (VM)
#--------------------------------------------------
@app.post('/destroy_env_vm')
async def call_destroy_env_vm(request: DestroyEnvVMRequest):
    try:
        logging.info(f"Received request data: {request}")
        # Call the function with the extracted data
        system_manager_api.destroy_user_env_vm(request.vm_name, request.macvlan_interface)
        return {"status": "success"}

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail='Failed to destroy VM environment')


#---------------------------------------------------------------
# User env 
#---------------------------------------------------------------
@app.post('/create_user_env_vm')
async def call_create_user_env_vm(request: CreateUserEnvVMRequest):
    try:
        logging.info(f"Received request data: {request}")

        # Call the function with the extracted data
        system_manager_api.create_user_env_vm(
            request.ubuntu_version,
            request.vm_name,
            request.root_size,
            request.user_info.dict()  # Convert Pydantic model to dictionary
        )
        return {"status": "User Env Created"}

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail='Failed to create VM environment')


#---------------------------------------------------------------
@app.post('/create_user')
async def create_user(request: CreateUser):
    try:
        logging.info(f"Received request data: {request}")
        # Call the function with the extracted data
        system_manager_api.allocate_active_users(request.user_name, request.user_network_id)
        return {"status": "User Created"}

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail='Failed to create User')


#---------------------------------------------------------------

@app.post('/clear_active_users')
def call_clear_active_users():
    try:
        system_manager_api.clear_active_users()
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail='Failed to clear active users list')

#---------------------------------------------------------------

# Fuction to reset the testbed(Turn off all nodes)

@app.post('/testbed_reset')
def call_testbed_reset():
    try:
        system_manager_api.testbed_reset()
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail='Failed to reset testbed')

#---------------------------------------------------------------

# Fuction to turn on all nodes

@app.post('/turn_on_all')
def call_turn_on_all_nodes():
    try:
        system_manager_api.turn_on_all_nodes()
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail='Failed to turn on all nodes')

#--------------------------------------------------------------


#---------------------------------------------------------------
#--------------------------------------------------
    
def run():
    uvicorn.run(app, host="localhost", port=8000)

run()
    
#-------------------------------------------------------------------------------------------------------------------
