# REST API Documentation (11 JUN 2024)

## Overview

This REST API, built with FastAPI, provides endpoints to manage system resources, user environments, testbed nodes, and Jetson devices.

## Endpoints

### Resource Management

#### Get Resource List

- **URL**: `/get_resource_list`
- **Method**: `POST`
- **Description**: Retrieves the list of available resources.
- **Responses**:
  - **200 OK**: Returns the resource list.
  - **500 Internal Server Error**: Failed to get resource list.

### User Environment Management

#### Destroy User Environment (VM)

- **URL**: `/destroy_env_vm`
- **Method**: `POST`
- **Description**: Destroys a user environment (VM).
- **Request Body**:
  - **vm_name**: Name of the VM.
  - **macvlan_interface**: MACVLAN interface.
- **Responses**:
  - **200 OK**: `{"status": "success"}`
  - **500 Internal Server Error**: Failed to destroy VM environment.

#### Create User Environment (VM)

- **URL**: `/create_user_env_vm`
- **Method**: `POST`
- **Description**: Creates a user environment (VM).
- **Request Body**:
  - **ubuntu_version**: Version of Ubuntu.
  - **vm_name**: Name of the VM.
  - **root_size**: Root size.
  - **user_info**: User information object containing user-specific details.
- **Responses**:
  - **200 OK**: Response details from the environment creation process.
  - **500 Internal Server Error**: Failed to create VM environment.

#### Stop User VM

- **URL**: `/stop_vm`
- **Method**: `POST`
- **Description**: Stops a running user VM.
- **Request Body**:
  - **vm_name**: Name of the VM.
- **Responses**:
  - **200 OK**: `{"status": "User vm stopped"}`
  - **500 Internal Server Error**: Failed to stop VM.

### User Management

#### Create User

- **URL**: `/create_user`
- **Method**: `POST`
- **Description**: Creates a new user.
- **Request Body**:
  - **user_name**: Name of the user.
  - **user_network_id**: Network ID of the user.
- **Responses**:
  - **200 OK**: `{"status": "User Created"}`
  - **500 Internal Server Error**: Failed to create user.

#### Clear Active Users

- **URL**: `/clear_active_users`
- **Method**: `POST`
- **Description**: Clears the list of active users.
- **Responses**:
  - **200 OK**: Active users list cleared.
  - **500 Internal Server Error**: Failed to clear active users list.

#### Get User Info

- **URL**: `/get_user_info`
- **Method**: `POST`
- **Description**: Retrieves user information.
- **Request Body**:
  - **user_name**: Name of the user.
  - **user_network_id**: Network ID of the user.
- **Responses**:
  - **200 OK**: User information.
  - **500 Internal Server Error**: Failed to get user information.

### Testbed Management

#### Reset Testbed

- **URL**: `/testbed_reset`
- **Method**: `POST`
- **Description**: Resets the testbed by turning off all nodes.
- **Responses**:
  - **200 OK**: Testbed reset.
  - **500 Internal Server Error**: Failed to reset testbed.

#### Turn On All Nodes

- **URL**: `/turn_on_all`
- **Method**: `POST`
- **Description**: Turns on all nodes.
- **Responses**:
  - **200 OK**: All nodes turned on.
  - **500 Internal Server Error**: Failed to turn on all nodes.

#### Turn On Specific Node

- **URL**: `/turn_on_node`
- **Method**: `POST`
- **Description**: Turns on a specific node.
- **Request Body**:
  - **node_name**: Name of the node.
- **Responses**:
  - **200 OK**: Node turned on.
  - **500 Internal Server Error**: Failed to turn on node.

#### Turn Off Specific Node

- **URL**: `/turn_off_node`
- **Method**: `POST`
- **Description**: Turns off a specific node.
- **Request Body**:
  - **node_name**: Name of the node.
- **Responses**:
  - **200 OK**: Node turned off.
  - **500 Internal Server Error**: Failed to turn off node.

### Jetson Management

#### Flash Jetson

- **URL**: `/flash_jetson`
- **Method**: `POST`
- **Description**: Flashes a Jetson device with specified configurations.
- **Request Body**:
  - **nfs_ip_addr**: NFS server IP address.
  - **nfs_path**: Path on the NFS server.
  - **usb_instance**: USB instance for flashing.
- **Responses**:
  - **200 OK**: Flashing details or success confirmation.
  - **500 Internal Server Error**: Failed to flash Jetson.

---



