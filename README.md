

# system-manager

This GitHub project is part of the testbed developed in the context of the 5G-mMTC (and NGC-AIoT) project. The **system-manager** handles low-level hardware and network functions on Jetson devices (Xavier and Nano) and exposes them via an API for other testbed components.

The testbed is designed with the following principles:
- **NFS Boot:** Each Jetson boots its root filesystem over NFS (running in a VM or container).
- **PoE Power:** Each Jetson is powered via PoE to enable remote reboot.
- **Recovery Mode:** Each Jetson is set to recovery mode to allow full control over booting and reinstallation.

![Network Architecture](docs/figs/final_network_arch.png)



---

##  Installation Procedure

This installation procedure first installs the Python dependencies using your setup.py (which pulls the latest configuration) and then automates the remainder of the installation using an Ansible playbook.

### Step 1: Install Python Dependencies

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your_org/system-manager.git
   cd system-manager
   ```

2. **Install Python Dependencies:**
   install first pip 
      ```bash
 
   sudo apt install python3-pip
      ```
   For a development (editable) install:
   ```bash
   pip install -e .
   ```

### Step 2: Download or Update the Configuration

After installing the Python dependencies, ensure that you have the latest configuration. If this is your first time or if you want to update, run the following commands:

1. **Initialize/Update the Configuration Submodule:**
   ```bash
   git submodule update --init --recursive
   ```

2. **Pull the Latest Configuration Updates:**
   ```bash
   git submodule update --remote --merge
   ```
   
   *Optional:* If you need only part of the configuration (e.g., only the system-manager folder), perform a sparse checkout:
   ```bash
   cd 5g-conf
   git sparse-checkout init --cone
   git sparse-checkout set system_manager README.md
   cd ../..
   ```

### Step 3: Automated Installation Using Ansible

The Ansible playbook automates the installation and configuration of the remaining components (such as LXD, BSP/rootfs extraction, and additional settings).

1. **Install Ansible:**
   ```bash
   sudo apt update && sudo apt install ansible -y
   ```

2. **Configure Network Settings:**

   Before running the playbook, update the network interface MAC address (if required) in:
   ```
   ansible/roles/server/vars/main.yml
   ```
   Update the `mac_address` field as needed.

3. **Run the Ansible Playbook:**
   
   From the repository root, execute:
   ```bash
   cd ansible
   ansible-playbook -i inventory.ini playbooks/site.yml --ask-become-pass
   ```
   This playbook will:
   - Install LXD and initialize it.
   - Set up LXD group permissions.
   - Download and extract the BSP and Rootfs packages.
   - Apply Jetson binaries and create the default user.
   - Download additional configuration files (such as rootfs tarball and NBD image files).

4. **Reboot the System:**

   After the playbook completes, reboot the system to apply all changes:
   ```bash
   sudo reboot
   ```

---

## Additional Configuration

### Switch Configuration

Before starting the system-manager API, verify that your network switch is configured correctly. For detailed instructions, see [docs/switch-config.md](docs/switch-config.md).

### Matching Jetson Devices to Switch Interfaces

Manually map each Jetson device to its corresponding switch interface. Use the `get_xavier_instances()` function from [`scripts/jetson_ctl.py`](scripts/jetson_ctl.py) to detect and map the devices.

### Running the System Manager API

Once installed and configured:

1. **Navigate to the API directory:**
   ```bash
   cd api
   ```

2. **Start the API service:**
   ```bash
   python3 system_manager_service.py
   ```

The API endpoints provided in [`system_manager_api.py`](api/system_manager_api.py) or the exported REST service will now be available.

---

## Docker and LXD Compatibility

If Docker is installed alongside LXD, networking issues might arise. To resolve these, add the following iptables rules:

1. **Allow communication from Docker to the LXD network:**
   ```bash
   iptables -I DOCKER-USER -i lxdbr0 -j ACCEPT
   ```

2. **Allow communication from the LXD network to Docker:**
   ```bash
   iptables -I DOCKER-USER -o lxdbr0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
   ```

If Docker is running, stop it to avoid conflicts:
```bash
sudo systemctl stop docker
```

Manual Configuration Details

For a full description of the manual configuration, please refer to docs/vm_server_config.md.   