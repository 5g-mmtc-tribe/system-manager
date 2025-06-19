# REST API Documentation (Updated: 19 JUN 2025)

## Overview

This REST API, built with FastAPI, manages system resources, user environments, testbed nodes, VLANs, and Jetson devices.

---

## Endpoints

### Resource Management

#### Get Resource List

* **URL**: `/get_resource_list`
* **Method**: `POST`
* **Description**: Retrieves the list of available resources from a JSON file.
* **Responses**:

  * `200 OK`: JSON list of resources.
  * `500 Internal Server Error`: Error loading resource list.

---

### User Environment Management

#### Create User Environment (VM)

* **URL**: `/create_user_env_vm`
* **Method**: `POST`
* **Description**: Creates a VM environment for a user and configures nodes if specified.
* **Request Body**:

  * `ubuntu_version` (string): Ubuntu version to use.
  * `vm_name` (string): Name of the VM.
  * `root_size` (string): Size of the root filesystem.
  * `user_info` (object): Contains `user_name`, `user_network_id`, `macvlan_interface`, and `nfs_ip_addr`.
  * `nodes` (list of strings): (Optional) List of nodes to configure NFS for.
* **Responses**:

  * `200 OK`: Information about the created environment.
  * `500 Internal Server Error`: Environment creation failed.

#### Destroy User Environment (VM)

* **URL**: `/destroy_env_vm`
* **Method**: `POST`
* **Description**: Destroys a user VM and deletes its macvlan interface.
* **Request Body**:

  * `vm_name` (string): Name of the VM.
  * `macvlan_interface` (string): Associated macvlan interface.
* **Responses**:

  * `200 OK`: `{"status": "success"}`
  * `500 Internal Server Error`: Failed to destroy VM.

#### Stop User VM

* **URL**: `/stop_vm`
* **Method**: `POST`
* **Description**: Stops a running VM.
* **Request Body**:

  * `vm_name` (string): Name of the VM.
* **Responses**:

  * `200 OK`: `{"status": "User vm stopped"}`
  * `500 Internal Server Error`: Stopping VM failed.

---

### User Management

#### Create User

* **URL**: `/create_user`
* **Method**: `POST`
* **Description**: Allocates a user and assigns network config.
* **Request Body**:

  * `user_name` (string)
  * `user_network_id` (int, 3–253)
* **Responses**:

  * `200 OK`: `{"status": "User Created"}`
  * `500 Internal Server Error`: Creation failed or ID already in use.

#### Clear Active Users

* **URL**: `/clear_active_users`
* **Method**: `POST`
* **Description**: Clears the active users JSON.
* **Responses**:

  * `200 OK`: `{"status": "Active users list cleared"}`
  * `500 Internal Server Error`: Failure to clear.

#### Get User Info

* **URL**: `/get_user_info`
* **Method**: `POST`
* **Description**: Retrieves details about a user.
* **Request Body**:

  * `user_name` (string)
  * `user_network_id` (int)
* **Responses**:

  * `200 OK`: JSON object with user details.
  * `500 Internal Server Error`: User not found.

---

### Testbed Management

#### Reset Testbed

* **URL**: `/testbed_reset`
* **Method**: `POST`
* **Description**: Turns off all testbed nodes (via PoE manager).
* **Responses**:

  * `200 OK`: Testbed reset.
  * `500 Internal Server Error`: Failure occurred.

#### Turn On All Nodes

* **URL**: `/turn_on_all`
* **Method**: `POST`
* **Description**: Turns on all testbed nodes.
* **Responses**:

  * `200 OK`: All nodes turned on.
  * `500 Internal Server Error`: Operation failed.

#### Turn On Specific Node

* **URL**: `/turn_on_node`
* **Method**: `POST`
* **Description**: Powers on a node via its switch interface.
* **Request Body**:

  * `node_name` (string): Name of the node (mapped to switch interface).
* **Responses**:

  * `200 OK`: Node powered on.
  * `500 Internal Server Error`: Error occurred.

#### Turn Off Specific Node

* **URL**: `/turn_off_node`
* **Method**: `POST`
* **Description**: Powers off a specific node.
* **Request Body**:

  * `node_name` (string)
* **Responses**:

  * `200 OK`: Node powered off.
  * `500 Internal Server Error`: Error occurred.

---

### Jetson Management

#### Flash Jetson

* **URL**: `/flash_jetson`
* **Method**: `POST`
* **Description**: Flashes a Jetson board with a specified image.
* **Request Body**:

  * `nfs_ip_addr` (string): NFS server IP.
  * `nfs_path` (string): NFS directory path.
  * `usb_instance` (string): USB instance to flash to.
* **Responses**:

  * `200 OK`: Success or details.
  * `500 Internal Server Error`: Flashing failed.

---

### VLAN and Switch Management

#### Attach VLAN to Interface

* **URL**: `/attach_vlan`
* **Method**: `POST`
* **Description**: Attaches a VLAN to a device switch interface.
* **Request Body**:

  * `device_name` (string)
  * `vlan_id` (int)
* **Responses**:

  * `200 OK`: VLAN attached.
  * `500 Internal Server Error`: Operation failed.

---

## Notes

* Most management operations use the PoE and Switch APIs behind the scenes (see: `SwitchManager`, `PoeManager`).
* Node and NFS setup logic is conditionally applied based on node type (Jetson, RPi, etc.).
* we use of config files: `SWITCH_CONFIG_PATH`, `RESOURCE_JSON_PATH`, etc.


