#-------------------------------------------------------------------------------------------------------------------
# Define the REST API and run with FastAPI,uvicorn
#-------------------------------------------------------------------------------------------------------------------

from fastapi import FastAPI, Request, HTTPException
import system_manager_api 
import logging
import uvicorn
from pydantic import BaseModel
from models import DestroyEnvVMRequest, CreateUser,  CreateUserEnvVMRequest ,TurnNode, VlanNode ,jetsonInfo ,sshInfo


logging.basicConfig(level=logging.ERROR)
app = FastAPI()

@app.get("/")
def read_root():
    return {" this is the systeme manager"} 
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
        resp=system_manager_api.create_user_env_vm(
            request.ubuntu_version,
            request.vm_name,
            request.root_size,
            request.user_info.dict()  # Convert Pydantic model to dictionary
        )
        return  resp

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail='Failed to create VM environment')

#---------------------------------------------------------------
# stop user vm  
#---------------------------------------------------------------
@app.post('/stop_vm')
async def call_create_stop_user_vm(request: DestroyEnvVMRequest):
    try:
        logging.info(f"Received request data: {request}")

        # Call the function with the extracted data
        system_manager_api.stop_user_vm(
            request.vm_name  # Convert Pydantic model to dictionary
        )
        return {"status": "User vm stopped"}

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail='Failed to stop  VM ')


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
# Fuction to turn  on specific node 

@app.post('/turn_on_node')
def call_turn_on_node(request:TurnNode):
    try:
        logging.info(f"Received request data: {request}")
        interface=system_manager_api.get_switch_interface(request.node_name)
        system_manager_api.turn_on_node(interface)
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail='Failed to turn on node')
    
# Fuction to turn off  specific node 

@app.post('/turn_off_node')
def call_turn_off_node(request:TurnNode):
    try:
        logging.info(f"Received request data: {request}")
        interface=system_manager_api.get_switch_interface(request.node_name)
        system_manager_api.turn_off_node(interface)
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail='Failed to turn off  node')
    
# fuction to put switch interface conneted to a device in the same vlan 
@app.post('/add_vlan_int')
def call_add_vlan_int(request: VlanNode):
    try:
        logging.info(f"Received request data: {request}")
        interface=system_manager_api.get_switch_interface(request.node_name)
        system_manager_api.attach_vlan_device_interface(interface ,request.vlan_id)
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail='Failed to ADD VLAN')
    

#--------------------------------------------------------------
# Function to get user info
#--------------------------------------------------------------

@app.post('/get_user_info')
async def call_get_user_info(request:CreateUser):
    try:
        logging.info(f"Received request data: {request}")
        # Call the function with the extracted data
        user_info = system_manager_api.get_user_info(request.user_name, request.user_network_id)
        return user_info

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail='Failed to create User')

#--------------------------------------------------------------
#--------------------------------------------------------------
# Function to ADD ssh pub key to the vm
#--------------------------------------------------------------

@app.post('/ssh_add')
async def call_ssh_add(request:sshInfo):
    try:
        logging.info(f"Received request data: {request}")
        # Call the function with the extracted data
        return system_manager_api.update_ssh(request.user_name)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail='Failed to flash jetson')
#--------------------------------------------------------------
# Function to flash jetson 
#--------------------------------------------------------------

@app.post('/flash_jetson')
async def call_flash_jetson(request:jetsonInfo):
    try:
        logging.info(f"Received request data: {request}")
        # Call the function with the extracted data
        flash_info = system_manager_api.flash_jetson(request.nfs_ip_addr ,request.nfs_path,request.usb_instance)
        return flash_info

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail='Failed to flash jetson')
#---------------------------------------------------------------
#--------------------------------------------------
    
def run():
    uvicorn.run(app, host="localhost", port=8083)

run()
    
#-------------------------------------------------------------------------------------------------------------------
