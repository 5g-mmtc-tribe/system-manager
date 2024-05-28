#-------------------------------------------------------------------------------------------------------------------
# Define the REST API and run with FastAPI,uvicorn
#-------------------------------------------------------------------------------------------------------------------

from fastapi import FastAPI, Request, HTTPException
import system_manager_api
import logging
import uvicorn

logging.basicConfig(level=logging.ERROR)
app = FastAPI()
app.post('/get_active_jetsons_list')(system_manager_api.get_active_jetsons_list)

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
