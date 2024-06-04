## system-manager
Interfaces to manage all the hardware components of the testbed


## Getting started

# Step 1: Installation (To be done once only)

     sudo snap install lxd --channel=latest/stable

# Step 2: LXD initialization

    lxd init --minimal

# Step 3: Navigate in the api folder

    cd system-manager/api

# Step 4: Run the system manager API

    python system_manager_service.py

### You can now use the API as shown in the examples in the file test_service.py


