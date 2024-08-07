# This Git-Hub project is part of the testbed developed in the context of the project 5G-mMTC (and NGC-AIoT).

The testbed itself includes several components, the "system-manager" is in charge of everything low-level which is 
specific to the hardware/networks and exports it through API for other components.

Initially, the focus is on managing a testbed of Jetson devices (Xavier and Nano).
Due to network/NFS boot issues on some Jetsons, and also for maximal manageability, the testbed is designed to work as
follows:
- each Jetson will have it root filesystem through NFS (itself in a VM or container)
- each Jetson is expected to be powered through PoE (in order to reboot)
- each Jetson is put in recovery mode (physical), to have full control of the booting/reinstall process

![network architecture](docs/figs/final_network_arch.jpeg)

## The `system-manager`

The system-manager provides an API for the user to manage all the hardware and software components of the testbed.
- It provides a Python API, through the `api/system_manager_api.py`. 
- This API can also be exported as a REST API service through `api/system_manager_service.py`

### Getting started

It is designed to be used as part of a large platform (with other components), and thus repackaged.
The steps below are only to run the `system-manager` standalone.

### Step 1: Installation 
(To be done once only)

     sudo snap install lxd --channel=latest/stable
     pip install fastapi

     Download 	the rootfs and the bsp for jeston flashing into 
        cd system-manager/data
        1. bsp
            wget https://developer.nvidia.com/downloads/embedded/l4t/r35_release_v4.1/release/jetson_linux_r35.4.1_aarch64.tbz2
        2. rootfs
            wget https://developer.nvidia.com/downloads/embedded/l4t/r35_release_v4.1/release/tegra_linux_sample-root-filesystem_r35.4.1_aarch64.tbz2

### Step 2: LXD initialization
(To be done once only)

    lxd init --minimal

### Step 3: Navigate in the /system-manager/api folder

    cd system-manager/api

### Step 4: Run the system manager API

    python system_manager_service.py


You can now use the API as shown in the examples in the file test_service.py
