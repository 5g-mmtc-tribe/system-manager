#-------------------------------------------------------------------------------------------------------------------
# Define the REST API and run with FastAPI,uvicorn
#-------------------------------------------------------------------------------------------------------------------

from fastapi import FastAPI, Request, HTTPException
import system_manager_api 
import logging
import uvicorn
from pydantic import BaseModel
from models import DestroyEnvVMRequest  


logging.basicConfig(level=logging.ERROR)
app = FastAPI()

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



@app.post('/create_env')
async def call_create_env(request: Request):
    try:
        config_json = await request.json()
        print("XXX TODO XXX")
        result = system_manager_api.create_env(config_json)
        return {"result": result}
    
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail='Failed to create environment')

#--------------------------------------------------
    
def run():
    uvicorn.run(app, host="localhost", port=8000)

run()
    
#-------------------------------------------------------------------------------------------------------------------
