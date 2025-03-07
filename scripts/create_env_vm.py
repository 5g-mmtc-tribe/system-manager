import subprocess
import time
import json
import os
import sys
import logging
from typing import Any, Optional

import pylxd
import redis
from macvlan import MacVlan

# Update sys.path for additional modules
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts'))
sys.path.append(SCRIPT_PATH)
from ip_addr_manager import IpAddr

USER_SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../user-scripts'))
SWITCH_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../switch'))
sys.path.append(SWITCH_PATH)
from switch_manager import SwitchManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class VmManager:
    """
    A class to manage Virtual Machines using LXC.
    """
    # Constants and paths
    current_dir: str = os.path.dirname(__file__)
    data_dir: str = os.path.join(current_dir, '../data')
    jetson_path: str = os.path.join(data_dir, 'jetson')
    bsp_path: str = os.path.join(data_dir, 'jetson_linux_r35.4.1_aarch64.tbz2')
    rootfs_path: str = os.path.join(data_dir, 'tegra_linux_sample-root-filesystem_r35.4.1_aarch64.tbz2')
    nbd_size: int = 16384

    # --------------------------------------------------------------------------
    # 1. Utility Functions
    # --------------------------------------------------------------------------
    @staticmethod
    def run_lxc_command(vm_name: str, command: list[str]) -> None:
        """
        Runs a command inside an LXC VM.
        """
        full_command = ["lxc", "exec", vm_name, "--"] + command
        try:
            result =subprocess.run(full_command, capture_output=True,check=True, text=True)
            logging.info("Command succeeded: %s", " ".join(command))
            return result
        except subprocess.CalledProcessError as e:
            logging.error("Command failed: %s. Error: %s", " ".join(command), e)
            raise

    @staticmethod
    def run_command(command: list[str], description: str) -> None:
        """
        Runs a shell command with a description.
        """
        logging.info("Running: %s", description)
        logging.info("Command: %s", " ".join(command))
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                logging.info(output.strip())
        stderr = process.communicate()[1]
        if stderr:
            logging.error(stderr)
        if process.returncode != 0:
            error_message = f"Command execution failed with return code {process.returncode}"
            logging.error(error_message)
            raise Exception(error_message)
        else:
            logging.info("Command executed successfully")

    # --------------------------------------------------------------------------
    # 2. VM State Checkers & Helpers
    # --------------------------------------------------------------------------
    def is_vm_running(self, vm_name: str) -> bool:
        """
        Checks if the given VM is running.
        """
        list_command = ["lxc", "list", vm_name, "--format", "json"]
        try:
            result = subprocess.run(list_command, capture_output=True, text=True, check=True)
            instances = json.loads(result.stdout)
            return bool(instances and instances[0]["name"] == vm_name and instances[0]["status"] == "Running")
        except subprocess.CalledProcessError as e:
            logging.error("Failed to execute command: %s", e)
            return False

    def is_vm_stopped(self, vm_name: str) -> bool:
        """
        Checks if the given VM is stopped.
        """
        list_command = ["lxc", "list", vm_name, "--format", "json"]
        try:
            result = subprocess.run(list_command, capture_output=True, text=True, check=True)
            instances = json.loads(result.stdout)
            return bool(instances and instances[0]["name"] == vm_name and instances[0]["status"] == "Stopped")
        except subprocess.CalledProcessError as e:
            logging.error("Failed to execute command: %s", e)
            return False

    def is_interface_up(self, vm_name: str, interface_name: str = "enp5s0") -> bool:
        """
        Checks if a specific network interface is present and up.
        """
        check_command = ["lxc", "exec", vm_name, "--", "ip", "-c", "a"]
        try:
            result = subprocess.run(check_command, capture_output=True, text=True, check=True)
            return interface_name in result.stdout
        except subprocess.CalledProcessError:
            return False

    def check_vm_exists(self, vm_name: str) -> bool:
        """
        Checks if the specified VM exists.
        """
        client = pylxd.Client()
        for instance in client.instances.all():
            if instance.name == vm_name and instance.type == 'virtual-machine':
                return True
        return False

    def get_vm_ip(self, vm_name: str) -> Optional[str]:
        """
        Retrieves the IP address of the VM using pylxd.
        """
        client = pylxd.Client()
        try:
            vm = client.virtual_machines.get(vm_name)
            network_info = vm.state().network
            interface = "enp5s0"
            for ip in network_info.get(interface, {}).get('addresses', []):
                if ip.get('family') == 'inet':
                    return ip.get('address')
        except Exception as e:
            logging.error("Error getting IP for VM %s: %s", vm_name, e)
        return None

    # --------------------------------------------------------------------------
    # 3. VM Lifecycle Management
    # --------------------------------------------------------------------------
    def create_user_vm(self, ubuntu_version: str, vm_name: str, root_size: str) -> dict[str, Any]:
        """
        Creates a new user VM if it does not already exist.
        Returns a dict indicating if the VM was created.
        """
        if self.check_vm_exists(vm_name):
            logging.info("VM %s already exists!", vm_name)
            return {"created": False}
        command = f"lxc launch ubuntu:{ubuntu_version} {vm_name} --vm --device root,size={root_size} -c limits.cpu=4 -c limits.memory=4GiB"
        logging.info("Executing command: %s", command)
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            logging.info("STDOUT: %s", result.stdout)
            return {"created": True}
        except subprocess.CalledProcessError as e:
            logging.error("Failed to create VM %s. Error: %s", vm_name, e)
            raise

    def start_vm(self, vm_name: str) -> int:
        """
        Starts the VM and waits until the network interface is up.
        Returns 0 if successful, 1 on timeout.
        """
        if not self.is_vm_running(vm_name):
            logging.info("Starting VM %s...", vm_name)
            subprocess.run(['lxc', 'start', vm_name], check=True)
            timeout = 30
            interval = 2
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.is_interface_up(vm_name, "enp6s0"):
                    logging.info("VM %s is running with an active network interface.", vm_name)
                    self.configure_vm_nat(vm_name)
                    return 0
                logging.info("Waiting for interface in VM %s to come up...", vm_name)
                time.sleep(interval)
            logging.warning("VM %s started, but network interface is still down.", vm_name)
            return 1
        else:
            logging.info("VM %s is already running!", vm_name)
            return 0

    def stop_vm(self, vm_name: str) -> None:
        """
        Stops the specified VM.
        """
        if not self.is_vm_stopped(vm_name):
            command = ['lxc', 'stop', vm_name, '--force']
            try:
                subprocess.run(command, check=True)
                logging.info("VM %s stopped successfully.", vm_name)
            except subprocess.CalledProcessError as e:
                logging.error("Failed to stop VM %s. Error: %s", vm_name, e)
                raise
        else:
            logging.info("VM %s is already stopped.", vm_name)

    def delete_vm(self, vm_name: str) -> None:
        """
        Deletes the specified VM.
        """
        if self.is_vm_running(vm_name):
            delete_command = ["lxc", "delete", vm_name, "--force"]
            try:
                subprocess.run(delete_command, capture_output=True, text=True, check=True)
                logging.info("VM %s has been deleted.", vm_name)
            except subprocess.CalledProcessError as e:
                logging.error("Failed to delete VM %s. Error: %s", vm_name, e)
                raise
        else:
            logging.info("VM %s is not running or does not exist.", vm_name)

    # --------------------------------------------------------------------------
    # 4. Network Configuration
    # --------------------------------------------------------------------------
    def configure_vm_nat(self, vm_name: str) -> None:
        """
        Enables IP forwarding and sets up NAT inside the VM.
        """
        commands = [
            "sysctl -w net.ipv4.ip_forward=1",
            "iptables -t nat -A POSTROUTING -o enp5s0 -j MASQUERADE"
        ]
        for cmd in commands:
            try:
                subprocess.run(['lxc', 'exec', vm_name, '--', 'sh', '-c', cmd], check=True)
                logging.info("Executed in %s: %s", vm_name, cmd)
            except subprocess.CalledProcessError as e:
                logging.error("Error configuring NAT in VM %s: %s", vm_name, e)
                raise

    def set_nfs_ip_addr(self, vm_name: str, nfs_ip_addr: str) -> None:
        """
        Configures the NFS IP address inside the VM.
        """
        interface_name = "enp6s0"
        if self.interface_check(vm_name, interface_name):
            command_check = ["lxc", "exec", vm_name, "--", "ip", "addr", "show", interface_name]
            try:
                result = subprocess.run(command_check, capture_output=True, text=True, check=True)
                if nfs_ip_addr in result.stdout:
                    logging.info("IP %s already set on %s; skipping update.", nfs_ip_addr, interface_name)
                    return
            except subprocess.CalledProcessError as e:
                logging.error("Failed to check IP address: %s", e)
                return

            ip = IpAddr()
            ip.update_network_config("ipconfig.txt", nfs_ip_addr)
            push_command = ["lxc", "file", "push", "ipconfig.txt", f"{vm_name}/root/"]
            self.run_command(push_command, "Copy NFS IP config")
            time.sleep(7)
            lxc_command = f"lxc exec {vm_name} -- sh -c \"cat /root/ipconfig.txt > /etc/netplan/50-cloud-init.yaml\""
            try:
                result = subprocess.run(lxc_command, shell=True, capture_output=True, text=True)
                logging.info("Updated netplan: %s", result.stdout)
            except subprocess.CalledProcessError as e:
                logging.error("Failed to update netplan: %s", e)
            disable_cloud_init = [
                "lxc", "exec", vm_name, "--", "sudo", "sh", "-c",
                "echo 'network: {config: disabled}' > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg"
            ]
            try:
                subprocess.run(disable_cloud_init, capture_output=True, text=True, check=True)
                logging.info("Disabled cloud-init network configuration.")
            except subprocess.CalledProcessError as e:
                logging.error("Failed to disable cloud-init: %s", e)
            netplan_apply = ["lxc", "exec", vm_name, "--", "sudo", "netplan", "apply"]
            logging.info("Applying netplan configuration: %s", " ".join(netplan_apply))
            try:
                subprocess.run(netplan_apply, capture_output=True, text=True, check=True)
                time.sleep(7)
                logging.info("Netplan applied successfully.")
            except subprocess.CalledProcessError as e:
                logging.error("Netplan apply failed: %s", e)

    def interface_check(self, vm_name: str, interface_name: str) -> bool:
        """
        Checks if a given interface is present in the VM.
        """
        command = ["lxc", "exec", vm_name, "--", "ip", "-c", "a"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            if interface_name in result.stdout:
                logging.info("Interface %s is present in VM %s.", interface_name, vm_name)
                return True
            logging.warning("Interface %s is not present in VM %s.", interface_name, vm_name)
            return False
        except subprocess.CalledProcessError as e:
            logging.error("Failed to check interface in VM %s. Error: %s", vm_name, e)
            return False

    # --------------------------------------------------------------------------
    # 5. MACVLAN Management
    # --------------------------------------------------------------------------
    def create_macvlan_for_vm(self, vm_name: str, network_id: int, switch_config: dict, interface_name: str, macvlan_name: str) -> None:
        """
        Adds a MACVLAN NIC to the VM and configures VLAN on the switch.
        """
        command = [
            "lxc", "config", "device", "add", vm_name, 'eth2', "nic",
            "nictype=macvlan", f"parent={interface_name}", f"vlan={network_id}"
        ]
        self.run_command(command, f"Adding eth2 NIC to VM '{vm_name}' with MACVLAN (VLAN {network_id})")
        device = switch_config
        switch = SwitchManager(
            device_type=device['device_type'],
            ip=device['ip'],
            port=device['port'],
            password=device['password']
        )
        switch.configure_vlan(network_id, f"vlan{network_id}")

    def delete_macvlan_for_vm(self, macvlan_manager: MacVlan, macvlan_name: str) -> None:
        """
        Deletes the MACVLAN if it exists.
        """
        if macvlan_manager.macvlan_exists(macvlan_name):
            macvlan_manager.delete_macvlan(macvlan_name)
            logging.info("Deleted MACVLAN %s", macvlan_name)
        else:
            logging.info("MACVLAN %s does not exist", macvlan_name)

    def attach_macvlan_to_vm(self, vm_name: str, macvlan_name: str) -> None:
        """
        Attaches a MACVLAN interface to the VM.
        """
        command = f"lxc config device add {vm_name} eth1 nic nictype=macvlan parent={macvlan_name}"
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            logging.info("Attached MACVLAN. STDOUT: %s", result.stdout)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to attach MACVLAN to VM %s. Error: %s", vm_name, e)
            raise

    # --------------------------------------------------------------------------
    # 6. DHCP & NFS Server Setup
    # --------------------------------------------------------------------------
    def create_dhcp_server(self, vm_name: str, nfs_ip_addr: str) -> None:
        """
        Installs and configures a DHCP server inside the VM.
        """
        install_command = ["lxc", "exec", vm_name, "--", "sudo", "apt", "install", "-y", "isc-dhcp-server"]
        self.run_command(install_command, "Install DHCP server")
        ip = IpAddr()
        ip.update_dhcp_configuration("dhcpConfig.txt", nfs_ip_addr)
        push_cmd = ["lxc", "file", "push", "dhcpConfig.txt", f"{vm_name}/root/"]
        self.run_command(push_cmd, "Copy DHCP config")
        lxc_cmd = f"lxc exec {vm_name} -- sh -c \"sudo cat /root/dhcpConfig.txt >> /etc/dhcp/dhcpd.conf\""
        try:
            subprocess.run(lxc_cmd, shell=True, capture_output=True, text=True, check=True)
            logging.info("DHCP config appended.")
        except subprocess.CalledProcessError as e:
            logging.error("Failed to update DHCP config: %s", e)
        for action in [("restart", "Restart DHCP server"), ("enable", "Enable DHCP server")]:
            cmd = ["lxc", "exec", vm_name, "--", "sudo", "systemctl", action[0], "isc-dhcp-server"]
            self.run_command(cmd, action[1])

    def create_nfs_server(self, vm_name: str, nfs_root: str ,driver:str) -> None:
        """
        Configures the NFS server inside the VM.
        """
         
        #nfs_root = "/root/nfsroot-jp-3541"
        #driver = 'rootfs-basic-jp3541-noeula-user.tar.gz'
        #driver = 'rootfs-basic-jp3541-with-docker-noeula-user.tar.gz'
        vmcmd = ["lxc", "exec", vm_name, "--", "sudo"]
        for folder in [nfs_root, f"{nfs_root}/rootfs"]:
            self.run_command(vmcmd + ["mkdir", folder],
                         f"Create folder {folder} in VM {vm_name}")
            
        vmcmd_no_sudo = ["lxc", "exec", vm_name, "--"]
        self.run_command(vmcmd_no_sudo + ["chown", "-R", "nobody:nogroup", f"{nfs_root}"],
                         "Change ownership of NFS folder")
        self.run_command(vmcmd_no_sudo + ["sudo", "chmod", "755", f"{nfs_root}"],
                         "Set permissions for NFS folder")
        tarball_cmd = ['lxc', 'file', 'push', driver, f'{vm_name}/root/']
        self.run_command(tarball_cmd, "Push rootfs tarball")
        extract_cmd = ['lxc', 'exec', vm_name, '--', 'tar', 'xpzf', f'/root/{driver}',
                       '-C', f'{nfs_root}/rootfs']
        self.run_command(extract_cmd, "Extract rootfs tarball")

        # Delete the driver tarball from the VM after extraction
        delete_cmd = ['lxc', 'exec', vm_name, '--', 'rm', '-f', f'/root/{driver}']
        self.run_command(delete_cmd, "Delete driver tarball after extraction")

        exports_cmd = f"echo '{nfs_root}/rootfs *(async,rw,no_root_squash,no_all_squash,no_subtree_check,insecure,anonuid=1000,anongid=1000)' > /etc/exports"
        lxc_exports = f"lxc exec {vm_name} -- sh -c \"{exports_cmd}\""
        try:
            subprocess.run(lxc_exports, shell=True, capture_output=True, text=True, check=True)
            logging.info("Updated /etc/exports in VM %s", vm_name)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to update /etc/exports: %s", e)
        self.run_command(["lxc", "exec", vm_name, "--", "sudo", "exportfs", "-a"],
                         "Refresh NFS exports")
        for action in [("restart", "Restart NFS server"), ("enable", "Enable NFS server")]:
            cmd = ["lxc", "exec", vm_name, "--", "sudo", "systemctl", action[0], "nfs-kernel-server"]
            self.run_command(cmd, action[1])

    # --------------------------------------------------------------------------
    # 7. Additional Configuration
    # --------------------------------------------------------------------------


    def _install_nbd_packages(self, vm_name: str) -> None:
        """
        Installs required packages and prepares the environment inside the VM.
        """
        commands = [
            ["apt", "update"],
            ["apt", "install", "-y", "nbd-server"],
            ["modprobe", "nbd"],
            ["sh", "-c", "echo 'nbd' >> /etc/modules"]
        ]
        for cmd in commands:
            self.run_lxc_command(vm_name, cmd)
        
        self.run_lxc_command(vm_name, ["mkdir", "-p", "/root/nbd_jetson"])
        logging.info("Created /root/nbd_jetson directory in VM %s", vm_name)
        self.run_lxc_command(vm_name, ["chmod", "755", "/root/nbd_jetson"])
 


    def _update_config_file(self, vm_name: str, nfs_server_ip: str, nodes: list) -> None:
        """
        Updates /etc/nbd-server/config with configuration sections for nodes
        that are missing. Checks if f"[nbd_jetson_<node>]\n" exists before appending.
        """
     
        result = self.run_lxc_command(
                vm_name, ["cat", "/etc/nbd-server/config"]
            )
        current_config = result.stdout
   
        new_sections = ""
        for node in nodes:
            header = f"[nbd_jetson_{node}]\n"
            if header not in current_config:
                section = (
                    header +
                    f"exportname = /root/nbd_jetson/nbd_jetson_{node}.img\n" +
                    "readonly = false\n" +
                    f"listenaddr = {nfs_server_ip}\n\n"
                )
                new_sections += section
            else:
                logging.info("Configuration for node %s already exists.", node)
        
        if new_sections:
            cmd = ["sh", "-c", f"echo '{new_sections}' >> /etc/nbd-server/config"]
            self.run_lxc_command(vm_name, cmd)
            logging.info("Updated config file with new sections:\n%s", new_sections)
        else:
            logging.info("No new config sections needed in /etc/nbd-server/config.")

    def _create_and_format_disk_image(self, vm_name: str, node: str) -> None:
        """
        Creates a disk image for the node and formats it as ext4 if it does not already exist.
        """
        image_path = f"/root/nbd_jetson/nbd_jetson_{node}.img"

        # Check if the disk image exists by trying to execute the test command.
        try:
            self.run_lxc_command(vm_name, ["test", "-f", image_path])
            print(f"Disk image already exists: {image_path}, skipping creation.")
            return
        except Exception:
            # The test command fails (expected when file does not exist).
            print(f"Disk image not found, creating new disk image: {image_path}")

        # Create disk image using the dd command.
        dd_cmd = ["dd", "if=/dev/zero", f"of={image_path}", "bs=1M", f"count={self.nbd_size}"]
        self.run_lxc_command(vm_name, dd_cmd)

        # Format the disk image as ext4.
        self.run_lxc_command(vm_name, ["mkfs.ext4", image_path])

    def _restart_nbd_server(self, vm_name: str) -> None:
        """
        Restarts the nbd-server service to apply the new configuration.
        """
        self.run_lxc_command(vm_name, ["systemctl", "restart", "nbd-server"])

    def configure_nbd_on_lxc_vm(self, vm_name: str, nfs_server_ip: str, nodes: list) -> None:
            """
            Configures nbprofile inside the LXC VM based on the provided nodes.
            Each node gets its own configuration section and disk image.
            """
            logging.info("Setting up nbprofile inside VM %s for nodes: %s", vm_name, nodes)
            
            # Install required packages and prepare the environment.
            self._install_nbd_packages(vm_name)
            current_config = "[generic]\nallowlist = true\n\n"
            self.run_lxc_command(
                vm_name, ["sh", "-c", f"echo '{current_config}' > /etc/nbd-server/config"]
            )
            
            # Update the configuration file with sections for nodes that are missing.
            self._update_config_file(vm_name, nfs_server_ip, nodes)
            
            # Create and format disk image for each node.
            for node in nodes:
                self._create_and_format_disk_image(vm_name, node)
            
            # Restart nbd-server to apply changes.
            self._restart_nbd_server(vm_name)
            
            logging.info("nbprofile setup completed in VM %s", vm_name)
    
    def update_nbd_config(self, vm_name: str, nfs_server_ip: str, nodes: list) -> None:
                    # Update the configuration file with sections for nodes that are missing.
            logging.info("Setting up nbprofile inside VM %s for new nodes: %s", vm_name, nodes)
            self._update_config_file(vm_name, nfs_server_ip, nodes)
            
            # Create and format disk image for each node.
            for node in nodes:
                self._create_and_format_disk_image(vm_name, node)
            
            # Restart nbd-server to apply changes.
            self._restart_nbd_server(vm_name)
            
            logging.info("nbprofile setup completed in VM %s", vm_name)

    def configure_nbd_on_lxc_vm_1(self, vm_name: str,nfs_server_ip:str , nodes: list) -> None:
        """
        Configures nbprofile inside the LXC VM based on the provided nodes.
        Each node gets its own configuration section and image file.
        """
        logging.info("Setting up nbprofile inside VM %s for nodes: %s", vm_name, nodes)
        
        # Install required packages and prepare the environment
        for cmd in [
            ["apt", "update"],
            ["apt", "install", "-y", "nbd-server"],
            ["modprobe", "nbd"],
            ["sh", "-c", "echo 'nbd' >> /etc/modules"],
            ["mkdir", "-p", "/root/nbd_jetson"],
            ["chmod", "755", "/root/nbd_jetson"]
        ]:
            self.run_lxc_command(vm_name, cmd)
        
        # Build the configuration file content dynamically based on nodes
        config_content = "[generic]\nallowlist = true\n\n"
        for node in nodes:
            config_content += f"[nbd_jetson_{node}]\n"
            config_content += f"exportname = /root/nbd_jetson/nbd_jetson_{node}.img\n"
            config_content += "readonly = false\n"
            config_content += f"listenaddr = {nfs_server_ip}\n\n"
        
        # Write the configuration file
        self.run_lxc_command(vm_name, ["sh", "-c", f"echo '{config_content}' > /etc/nbd-server/config"])
        
        # Create a disk image and format it for each node
        for node in nodes:
            dd_cmd = [
                "dd", "if=/dev/zero",
                f"of=/root/nbd_jetson/nbd_jetson_{node}.img",
                "bs=1M", f"count={self.nbd_size}"
            ]
            self.run_lxc_command(vm_name, dd_cmd)
            self.run_lxc_command(vm_name, ["mkfs.ext4", f"/root/nbd_jetson/nbd_jetson_{node}.img"])
        
        # Restart the nbd-server to apply the changes
        self.run_lxc_command(vm_name, ["systemctl", "restart", "nbd-server"])
        logging.info("nbprofile setup completed in VM %s", vm_name)


    def add_torch_script(self, vm_name: str, src_script_path: str) -> None:
        """
        Adds a torch installation script to the VM.
        """
        try:
            subprocess.run(['lxc', 'file', 'push', src_script_path, f'{vm_name}/root/install_torch'],
                           check=True)
            logging.info("Torch script copied to VM %s", vm_name)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to add torch script: %s", e)
            raise

    # --------------------------------------------------------------------------
    # 8. SSH Key Management
    # --------------------------------------------------------------------------
    def add_ssh_key_to_lxd(self, username: str, lxd_vm_name: str) -> None:
        """
        Adds SSH public keys to the VM's authorized_keys file.
        """
        index_name = 'UserIdxs'
        redis_client = redis.Redis(host='localhost', port=6379)
        search_results = redis_client.ft(index_name).search(f"@login:({username})")
        if not search_results.docs:
            raise ValueError(f"No user found with login: {username}")
        user_data = json.loads(search_results.docs[0].json)
        ssh_keys = user_data.get('user', {}).get('sshKeys', [])
        if not ssh_keys:
            raise ValueError("No SSH keys found for the user")
        ssh_dir = "/root/.ssh"
        authorized_keys_file = f"{ssh_dir}/authorized_keys"
        subprocess.run(
            ['lxc', 'exec', lxd_vm_name, '--', 'bash', '-c',
             f'if [ ! -d "{ssh_dir}" ]; then mkdir -p "{ssh_dir}"; fi'], check=True)
        try:
            result = subprocess.run(
                ['lxc', 'exec', lxd_vm_name, '--', 'bash', '-c', f'cat {authorized_keys_file}'],
                capture_output=True, text=True, check=True)
            existing_keys = result.stdout.splitlines()
        except subprocess.CalledProcessError:
            existing_keys = []
        new_keys = [key for key in ssh_keys if key not in existing_keys]
        if new_keys:
            keys_to_add = "\n".join(new_keys)
            subprocess.run(
                ['lxc', 'exec', lxd_vm_name, '--', 'bash', '-c',
                 f'echo "{keys_to_add}" >> {authorized_keys_file}'], check=True)
            logging.info("Added new SSH keys to %s in VM %s", authorized_keys_file, lxd_vm_name)
        else:
            logging.info("No new SSH keys to add in VM %s", lxd_vm_name)
        for cmd in [
            ['chmod', '700', ssh_dir],
            ['chmod', '600', authorized_keys_file],
            ['chown', 'root:root', ssh_dir],
            ['chown', 'root:root', authorized_keys_file]
        ]:
            subprocess.run(['lxc', 'exec', lxd_vm_name, '--'] + cmd, check=True)
        logging.info("SSH key verification and update complete for VM %s", lxd_vm_name)
    import os

    def push_files_to_vm(self, vm_name, nfs_root, user_script_path, nfs_ip_addr):
        """
        Push multiple files to the VM in a single function.

        Parameters:
        - vm_name: Name of the virtual machine.
        - nfs_root: The NFS root directory path.
        - user_script_path: The local folder path where the scripts are stored.
        - nfs_ip_addr: IP address for network file system operations.
        """

        # Define the target directory in the VM
        target_dir = f"{vm_name}{nfs_root}/rootfs/home/mmtc/"

        # List of files with their corresponding descriptions.
        # For files that are part of the user_script_path, we join the path.
        # The Docker images file is assumed to be in the current directory.
        files_to_push = [
            ("Dockerfile", "Push Dockerfile to user home"),
            ("lib_setup.sh", "Push Jetson setup script to user home"),
            ("jetson_setup.sh", "Push jetson setup script"),
            ("restart_jetson.sh", "Push restart jetson setup script"),
            ("configure_PPP.sh", "Push configure PPP script"),
            ("fan_control.py", "Push fan control script"),
            ("mmtc-docker.tar", "Push Docker images")  # Assumed to be in the current working directory
        ]

        # Loop through each file and push it to the target directory
        for file_name, description in files_to_push:
            if file_name == "mmtc-docker.tar":
                # For the docker image tar file, the file is in the current folder.
                file_path = file_name
            else:
                # For all other files, use the user_script_path
                file_path = os.path.join(user_script_path, file_name)

            # Build the command list for pushing the file
            push_command = ["lxc", "file", "push", file_path, target_dir]
            self.run_command(push_command, description)

        # Create a readme in the VM after pushing all files
        VmManager.create_readme_in_vm(vm_name, nfs_ip_addr,nfs_root)

    # --------------------------------------------------------------------------
    # 9. Tool Installation
    # --------------------------------------------------------------------------
    def install_library_for_flashing_jetson(self, vm_name: str, nfs_ip_addr: str ) -> None:
        """
        Installs necessary libraries and scripts in the VM for flashing Jetson devices.
        """
        #nfs_root ="/root/nfsroot-jp-3541"
        self.run_command(["lxc", "exec", vm_name, "--", "sudo", "apt", "update"], "Update apt")
        install_binutils = ["lxc", "exec", vm_name, "--", "apt", "install", "-y", "binutils"]
        self.run_command(install_binutils, "Install binutils")
        install_nfs = ["lxc", "exec", vm_name, "--", "sudo", "apt", "install", "-y", "nfs-kernel-server"]
        self.run_command(install_nfs, "Install NFS server")
        push_5gmmtctool = ["lxc", "file", "push", os.path.join(USER_SCRIPT_PATH, "5gmmtctool"), f"{vm_name}/root/"]
        self.run_command(push_5gmmtctool, "Push 5gmmtctool")

        #self.add_torch_script(vm_name, "install_torch.sh")
        
    
    def folder_exists(self, vm_name: str, folder: str) -> bool:
        """
        Checks if the folder specified by nfs_root exists in the LXC container.
        
        For example, if nfs_root is "/mnt/nfs", this function runs:
            lxc file list <vm_name>/mnt/nfs
        and returns True if the folder exists.
        """
        # Construct the command using the container name and the folder path.
        check_command = ["lxc", "file", "list", f"{vm_name}{folder}"]
        try:
            # Attempt to list the folder contents.
            self.run_command(check_command, f"Check for folder {folder}", capture_output=True)
            return True
        except Exception:
            # If an error occurs (folder not found), return False.
            return False
            
    def configure_nfs_jetson(self ,vm_name: str, nfs_ip_addr: str ,nfs_root:str ,driver :str):
        if self.folder_exists(vm_name, nfs_root):
            print(f"Folder {nfs_root} already exists in container {vm_name}. Skipping configuration steps.")
            return
        self.create_nfs_server(vm_name, nfs_root,driver)
        push_nfs_setup = ["lxc", "file", "push", os.path.join(USER_SCRIPT_PATH, "nfs_setup.sh"), f"{vm_name}/root/"]
        self.run_command(push_nfs_setup, "Push NFS setup script")
        self.push_files_to_vm(vm_name,nfs_root,USER_SCRIPT_PATH,nfs_ip_addr)
        time.sleep(10)


    

    def install_5gmmtctool(self, vm_name: str, nfs_ip_addr: str) -> None:
        """
        Installs the 5gmmtctool and updates DHCP configuration.
        """
        ip = IpAddr()
        ip.update_dhcp_configuration("dhcpConfig.txt", nfs_ip_addr)
        push_cmd = ["lxc", "file", "push", "dhcpConfig.txt", f"{vm_name}/root/"]
        self.run_command(push_cmd, "Push DHCP configuration")
        push_tool = ["lxc", "file", "push", os.path.join(USER_SCRIPT_PATH, "5gmmtctool"), f"{vm_name}/root/"]
        self.run_command(push_tool, "Push 5gmmtctool")

    # --------------------------------------------------------------------------
    # 10. NFS Jetson Setup
    # --------------------------------------------------------------------------
    def setup_nfs_jetson(self, vm_name: str, nfsroot_v: str, device_names: list[str]) -> None:
        """
        Executes the NFS setup script inside the VM with provided nfsroot_v and device names.
        
        Usage:
        setup_nfs_jetson("<VM_NAME>", "<nfsroot-v>", ["device1", "device2", ...])
        """
        if not vm_name or not nfsroot_v or not device_names:
            logging.error("Usage: setup_nfs_jetson('<VM_NAME>', '<nfsroot-v>', ['device1', 'device2', ...])")
            return

        script_path = "/root/nfs_setup.sh"
        # First argument is now the nfsroot_v, followed by the device names
        args = " ".join([nfsroot_v] + device_names)
        
        try:
            subprocess.run(["lxc", "exec", vm_name, "--", "chmod", "+x", script_path], check=True)
            logging.info("Executing NFS setup script in VM %s", vm_name)
            subprocess.run(["lxc", "exec", vm_name, "--", "bash", "-c", f"{script_path} {args}"], check=True)
            logging.info("NFS setup script executed successfully in VM %s", vm_name)
        except subprocess.CalledProcessError as e:
            logging.error("Error executing NFS setup in VM %s: %s", vm_name, e)
            raise
    # --------------------------------------------------------------------------
    # 11. Utility: README Creation
    # --------------------------------------------------------------------------
    @staticmethod
    def create_readme_in_vm(vm_name: str, nfs_ip_addr: str, rootfs:str)  -> None:
        """
        Creates a README.md file inside the VM with setup instructions.
        """
    
        nfs_ip = nfs_ip_addr.split('/')[0]
        content = f"""# Setup Instructions
        
- Run lib_setup.sh to install required libraries.
- Run jetson_setup.sh with your NFS IP address:
    ./jetson_setup.sh {nfs_ip}

Replace {nfs_ip} with your actual NFS IP address.
"""    
        touch_cmd = f'lxc exec {vm_name} -- bash -c "touch {rootfs}/rootfs/home/mmtc/README.md"'
        try:
            subprocess.run(touch_cmd, shell=True, check=True)
            logging.info("Created README.md in VM %s", vm_name)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to create README.md: %s", e)
            raise
        write_cmd = (
            f'lxc exec {vm_name} -- bash -c "cat > {rootfs}/rootfs/home/mmtc/README.md << \'EOF\'\n'
            f'{content}\nEOF"'
        )
        try:
            subprocess.run(write_cmd, shell=True, check=True)
            logging.info("Populated README.md in VM %s", vm_name)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to write to README.md: %s", e)
            raise

# --------------------------------------------------------------------------
# 12. External Function: Jetson Setup
# --------------------------------------------------------------------------
def setup_jetson(base_dir: str, username: str, password: str, hostname: str) -> None:
    """
    Sets up the Jetson environment by extracting files, applying binaries, and compressing the root filesystem.
    """
    try:
        jetson_tar = os.path.join(base_dir, "Jetson_Linux_R35.4.1_aarch64.tbz2")
        tegra_tar = os.path.join(base_dir, "Tegra_Linux_Sample-Root-Filesystem_R35.4.1_aarch64.tbz2")
        output_dir = os.path.join("api", "jetson")
        os.makedirs(output_dir, exist_ok=True)
        logging.info("Extracting Jetson Linux package...")
        subprocess.run(["sudo", "tar", "-xf", jetson_tar, "-C", output_dir], check=True)
        logging.info("Extracting Tegra root filesystem...")
        tegra_rootfs = os.path.join(output_dir, "Linux_for_Tegra", "rootfs")
        os.makedirs(tegra_rootfs, exist_ok=True)
        subprocess.run(["sudo", "tar", "xpf", tegra_tar, "-C", tegra_rootfs], check=True)
        logging.info("Installing dependencies for binaries...")
        subprocess.run(["sudo", "add-apt-repository", "universe"], check=True)
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", "qemu-user-static"], check=True)
        logging.info("Applying binaries...")
        apply_binaries_script = os.path.join(output_dir, "Linux_for_Tegra", "apply_binaries.sh")
        subprocess.run(["sudo", apply_binaries_script], check=True)
        logging.info("Installing additional dependencies...")
        subprocess.run(["sudo", "apt-get", "install", "-y", "lz4", "libxml2-utils"], check=True)
        logging.info("Creating default user...")
        create_user_script = os.path.join(output_dir, "Linux_for_Tegra", "tools", "l4t_create_default_user.sh")
        subprocess.run([
            "sudo", create_user_script,
            "-u", username, "-p", password, "-n", hostname, "--accept-license"
        ], check=True)
        tarball_path = os.path.join("api", "rootfs-noeula-user.tar.gz")
        logging.info("Compressing root filesystem to %s...", tarball_path)
        subprocess.run(["sudo", "tar", "czvf", tarball_path, "-C", tegra_rootfs, "."], check=True)
        logging.info("Jetson setup completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error("Error during Jetson setup. Command: %s, Output: %s", e.cmd, e.output)
        raise

# Example usage 
# ubuntu_version = "24.04"
#
#  vm_name = "testvm"
# root_size = "4GiB"
# user_info = {
#     "user_name": "testvm",
#     "user_network_id": 75,
#     "user_subnet": "192.168.75.0/24",
#     "nfs_ip_addr": "192.168.75.1/24",
#     "macvlan_interface": "macvlan_testvm",
# }
vm_manager = VmManager()
# vm_manager.create_user_vm(ubuntu_version, vm_name, root_size)
# vm_manager.set_nfs_ip_addr(vm_name, user_info["nfs_ip_addr"])


#current_config = "[generic]\nallowlist = true\n\n"
#vm_manager.run_lxc_command(
#    "mehdi", ["sh", "-c", f"echo '{current_config}' > /etc/nbd-server/config"]
#)
#push_docker_images = ["lxc", "file", "push", "mmtc-docker.tar", f"{"mehdi"}/root/nfsroot-jp-3541/rootfs/home/mmtc/"]
#vm_manager.run_command(push_docker_images, "Push Docker images")
#push_nfs_setup = ["lxc", "file", "push", os.path.join(USER_SCRIPT_PATH, "nfs_setup.sh"), f"{"mehdi"}/root/"]
#vm_manager.run_command(push_nfs_setup, "Push NFS setup script")
#vm_manager.setup_nfs_jetson("mehdi",["j20-tribe2"])