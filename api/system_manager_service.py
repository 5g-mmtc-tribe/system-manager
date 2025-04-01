from fastapi import FastAPI, Request, HTTPException
from config import API_HOST, API_PORT, SYSTEM_MANAGER_LOG_FILE
import system_manager_api
import logging
import uvicorn
import time
import os
from pydantic import BaseModel
from models import (
    DestroyEnvVMRequest,
    CreateUser,
    CreateUserEnvVMRequest,
    TurnNode,
    VlanNode,
    jetsonInfo,
    sshInfo,
    Ressource
)
os.makedirs('../logs', exist_ok=True)
# Configure logging
logging.basicConfig(filename=SYSTEM_MANAGER_LOG_FILE, force=True,level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Logging is configured and file is in the logs folder.")

# Add a stream handler to also display logs in the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)
# Initialize FastAPI app
app = FastAPI(title="System Manager API", description="REST API for managing testbed environments", version="1.0")

@app.get("/", summary="Root Endpoint", description="Basic endpoint to check if the system manager is running.")
def read_root():
    return {"message": "This is the system manager"}

#--------------------------------------------------
# Get Resource List
#--------------------------------------------------
@app.post('/get_resource_list', summary="Get Resource List", description="Retrieve the list of resources from the system.")
def call_get_resource_list():
    try:
        resource_list = system_manager_api.get_resource_list()
        return resource_list
    except Exception as e:
        logging.error("Error retrieving resource list: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get resource list")


#--------------------------------------------------
# Update Resource 
#--------------------------------------------------
@app.post('/get_resource_update', summary=" get update  Resource info", description="Update resources from the system.")
def call_update_resource(request:Ressource):
    try:
        resource_list = system_manager_api.update_resource(request.name)
        return resource_list
    except Exception as e:
        logging.error("Error updating resource: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update resource ")
#--------------------------------------------------
# Destroy User Environment (VM)
#--------------------------------------------------
@app.post('/destroy_env_vm', summary="Destroy VM Environment", description="Destroy a user's VM environment.")
async def call_destroy_env_vm(request: DestroyEnvVMRequest):
    try:
        logging.info("Destroy VM request: %s", request)
        system_manager_api.destroy_user_env_vm(request.vm_name, request.macvlan_interface)
        return {"status": "success"}
    except Exception as e:
        logging.error("Error destroying VM environment: %s", e)
        raise HTTPException(status_code=500, detail="Failed to destroy VM environment")

#--------------------------------------------------
# Create User Environment (VM)
#--------------------------------------------------
@app.post('/create_user_env_vm', summary="Create VM Environment", description="Create a VM environment for a user.")
async def call_create_user_env_vm(request: CreateUserEnvVMRequest):
    try:
        logging.info("Create VM request: %s", request)
        response = system_manager_api.create_user_env_vm(
            request.ubuntu_version,
            request.vm_name,
            request.root_size,
            request.user_info.dict(),  # Convert Pydantic model to dict
            request.nodes
        )
        time.sleep(2)
        return response
    except Exception as e:
        logging.error("Error creating VM environment: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create VM environment")

#--------------------------------------------------
# Stop User VM
#--------------------------------------------------
@app.post('/stop_vm', summary="Stop VM", description="Stop a running user VM.")
async def call_stop_user_vm(request: DestroyEnvVMRequest):
    try:
        logging.info("Stop VM request: %s", request)
        system_manager_api.stop_user_vm(request.vm_name)
        return {"status": "User VM stopped"}
    except Exception as e:
        logging.error("Error stopping VM: %s", e)
        raise HTTPException(status_code=500, detail="Failed to stop VM")

#--------------------------------------------------
# Create User (Allocate Active User)
#--------------------------------------------------
@app.post('/create_user', summary="Create User", description="Allocate a new active user in the testbed.")
async def create_user(request: CreateUser):
    try:
        logging.info("Create user request: %s", request)
        system_manager_api.allocate_active_users(request.user_name, request.user_network_id)
        return {"status": "User Created"}
    except Exception as e:
        logging.error("Error creating user: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create user")

#--------------------------------------------------
# Clear Active Users List
#--------------------------------------------------
@app.post('/clear_active_users', summary="Clear Active Users", description="Clear the list of active users.")
def call_clear_active_users():
    try:
        system_manager_api.clear_active_users()
        return {"status": "Active users list cleared"}
    except Exception as e:
        logging.error("Error clearing active users list: %s", e)
        raise HTTPException(status_code=500, detail="Failed to clear active users list")

#--------------------------------------------------
# Testbed Reset (Turn Off All Nodes)
#--------------------------------------------------
@app.post('/testbed_reset', summary="Reset Testbed", description="Reset the testbed by turning off all nodes.")
def call_testbed_reset():
    try:
        system_manager_api.testbed_reset()
        return {"status": "Testbed reset initiated"}
    except Exception as e:
        logging.error("Error resetting testbed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to reset testbed")

#--------------------------------------------------
# Turn On All Nodes
#--------------------------------------------------
@app.post('/turn_on_all', summary="Turn On All Nodes", description="Turn on all nodes in the testbed.")
def call_turn_on_all_nodes():
    try:
        system_manager_api.turn_on_all_nodes()
        return {"status": "All nodes turned on"}
    except Exception as e:
        logging.error("Error turning on all nodes: %s", e)
        raise HTTPException(status_code=500, detail="Failed to turn on all nodes")

#--------------------------------------------------
# Turn On Specific Node
#--------------------------------------------------
@app.post('/turn_on_node', summary="Turn On Node", description="Turn on a specific node by name.")
def call_turn_on_node(request: TurnNode):
    try:
        logging.info("Turn on node request: %s", request)
        interface = system_manager_api.get_switch_interface(request.node_name)
        system_manager_api.turn_on_node(interface)
        return {"success": True}
    except Exception as e:
        logging.error("Error turning on node: %s", e)
        raise HTTPException(status_code=500, detail="Failed to turn on node")

#--------------------------------------------------
# Turn Off Specific Node
#--------------------------------------------------
@app.post('/turn_off_node', summary="Turn Off Node", description="Turn off a specific node by name.")
def call_turn_off_node(request: TurnNode):
    try:
        logging.info("Turn off node request: %s", request)
        interface = system_manager_api.get_switch_interface(request.node_name)
        system_manager_api.turn_off_node(interface)
        return {"success": True}
    except Exception as e:
        logging.error("Error turning off node: %s", e)
        raise HTTPException(status_code=500, detail="Failed to turn off node")

#--------------------------------------------------
# Add VLAN to Node
#--------------------------------------------------
@app.post('/add_vlan_int', summary="Add VLAN to Node", description="Attach a VLAN to the switch interface connected to a node.")
def call_add_vlan_int(request: VlanNode):
    try:
        logging.info("Add VLAN request: %s", request)
        interface = system_manager_api.get_switch_interface(request.node_name)
        system_manager_api.attach_vlan_device_interface(interface, request.vlan_id)
        #return {"status": f"VLAN {request.vlan_id} added to node '{request.node_name}'"}
        return {"success": True, "vlan_id": "request.vlan_id"}
    except Exception as e:
        logging.error("Error adding VLAN: %s", e)
        raise HTTPException(status_code=500, detail="Failed to add VLAN")

#--------------------------------------------------
# Get User Information
#--------------------------------------------------
@app.post('/get_user_info', summary="Get User Info", description="Retrieve information about a specific active user.")
async def call_get_user_info(request: CreateUser):
    try:
        logging.info("Get user info request: %s", request)
        user_info = system_manager_api.get_user_info(request.user_name, request.user_network_id)
        return user_info
    except Exception as e:
        logging.error("Error retrieving user info: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve user info")

#--------------------------------------------------
# Add SSH Public Key to VM
#--------------------------------------------------
@app.post('/ssh_add', summary="Add SSH Key", description="Add an SSH public key to a VM for the given user.")
async def call_ssh_add(request: sshInfo):
    try:
        logging.info("SSH add request: %s", request)
        return system_manager_api.update_ssh(request.user_name)
    except Exception as e:
        logging.error("Error adding SSH key: %s", e)
        raise HTTPException(status_code=500, detail="Failed to add SSH key")

#--------------------------------------------------
# Flash Jetson Device
#--------------------------------------------------
@app.post('/flash_jetson', summary="Flash Jetson", description="Flash a Jetson device using the provided parameters.")
async def call_flash_jetson(request: jetsonInfo):
    try:
        logging.info("Flash jetson request: %s", request)
        flash_info = system_manager_api.flash_jetson(
            request.nfs_ip_addr,
            request.nfs_path,
            request.usb_instance,
            request.switch_interface,
            request.model ,
            request.nvidia_id
        )
        return flash_info
    except Exception as e:
        logging.error("Error flashing jetson: %s", e)
        raise HTTPException(status_code=500, detail="Failed to flash jetson")

#--------------------------------------------------
# Main: Run API with Uvicorn
#--------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)
