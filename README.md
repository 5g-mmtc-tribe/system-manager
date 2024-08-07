# system-manager

The system-manager provides an API for the user to manage all the hardware and software components of the testbed.


## Getting started

## Step 1: Installation 
(To be done once only)

     sudo snap install lxd --channel=latest/stable
     pip install fastapi

     Download 	the rootfs and the bsp for jeston flashing into 
        cd system-manager/data
        1. bsp

        wget https://developer.nvidia.com/downloads/embedded/l4t/r35_release_v4.1/release/jetson_linux_r35.4.1_aarch64.tbz2


        2. rootfs


            wget https://developer.nvidia.com/downloads/embedded/l4t/r35_release_v4.1/release/tegra_linux_sample-root-filesystem_r35.4.1_aarch64.tbz2

## Step 2: LXD initialization
(To be done once only)

    lxd init --minimal

## Step 3: Navigate in the /system-manager/api folder

    cd system-manager/api

## Step 4: Run the system manager API

    python system_manager_service.py


You can now use the API as shown in the examples in the file test_service.py


