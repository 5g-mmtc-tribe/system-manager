import subprocess
import time
import json
import os
import sys
import logging
from typing import Any, Optional
import pylxd
import redis
from config import DHCP_CONFIG_FILE_PATH, DRIVER_SERVER_IP, IP_CONFIG_FILE_PATH, JETSON_SETUP_NFS, JTX2_CONFIG_FILE_PATH,  REDIS_HOST, REDIS_PORT, REDIS_USER_INDEX, ROOT_FS_RPI4, RPI4_SETUP_NFS, VM_INTERFACE ,USER_SCRIPT_PATH ,TOOLS_SCRIPT_PATH ,NBD_SIZE
from config.constants import BASE_IMAGE_J10, BASE_IMAGE_J20_J40, BASE_IMAGE_JTX ,NBD_IMAGE_NAME_J10, NBD_IMAGE_NAME_J20_J40, NBD_IMAGE_NAME_JTX, ROOT_FS_3274, RPI4_CONFIG_FILE_PATH
from scripts.macvlan import MacVlan
from scripts.ip_addr_manager import IpAddr
from switch.switch_manager import SwitchManager


# Setup module-level logger
logger = logging.getLogger(__name__)
class VmManager:
    """
    A class to manage Virtual Machines using LXC.
    """




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
    def folder_exists(self, vm_name: str, folder: str) -> bool:
        """
        Checks if the folder specified by nfs_root exists in the LXC container.
        
        For example, if nfs_root is "/mnt/nfs", this function runs:
            lxc file list <vm_name>/mnt/nfs
        and returns True if the folder exists.
        """
        # Construct the command using the container name and the folder path.
        check_command = ["lxc", "exec", vm_name, "--", "test", "-d", folder]
        try:
            # Attempt to check if the directory exists inside the container.
            self.run_command(check_command, f"Check if directory {folder} exists")
            return True
        except Exception:
            # If the command fails (i.e., the folder doesn't exist), return False.
            return False
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
                if self.is_interface_up(vm_name, VM_INTERFACE):
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
        interface_name = VM_INTERFACE
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
            ip.update_network_config(IP_CONFIG_FILE_PATH, nfs_ip_addr)
            push_command = ["lxc", "file", "push", IP_CONFIG_FILE_PATH, f"{vm_name}/root/"]
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
        push_rpi_config = ["lxc", "file", "push",RPI4_CONFIG_FILE_PATH, f"{vm_name}/etc/dhcp/"]
        self.run_command(push_rpi_config, "Copy rpi config")
        push_jtx_config = ["lxc", "file", "push",JTX2_CONFIG_FILE_PATH, f"{vm_name}/etc/dhcp/"]
        self.run_command(push_jtx_config, "push_jtx_config")
        ip.update_dhcp_configuration(DHCP_CONFIG_FILE_PATH, nfs_ip_addr)
        push_cmd = ["lxc", "file", "push",DHCP_CONFIG_FILE_PATH, f"{vm_name}/root/"]
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

    def create_nfs_server(self, vm_name: str, nfs_root: str ,driver:str ,driver_path:str) -> None:
        """
        Configures the NFS server inside the VM.
        """
        vmcmd = ["lxc", "exec", vm_name, "--", "sudo"]
        for folder in [nfs_root, f"{nfs_root}/rootfs"]:
            self.run_command(vmcmd + ["mkdir", folder],
                         f"Create folder {folder} in VM {vm_name}")
            
        vmcmd_no_sudo = ["lxc", "exec", vm_name, "--"]
        self.run_command(vmcmd_no_sudo + ["chown", "-R", "nobody:nogroup", f"{nfs_root}"],
                         "Change ownership of NFS folder")
        self.run_command(vmcmd_no_sudo + ["sudo", "chmod", "755", f"{nfs_root}"],
                         "Set permissions for NFS folder")
        tarball_cmd = ['lxc', 'file', 'push', driver_path, f'{vm_name}/root/']
        self.run_command(tarball_cmd, "Push rootfs tarball")
        if nfs_root == ROOT_FS_3274 :
            extract_cmd = ['lxc', 'exec', vm_name, '--', 'tar', 'xpzf', f'/root/{driver}','-C', f'{nfs_root}/rootfs'] #fro nano
        else :
            extract_cmd = [
            'lxc', 'exec', vm_name, '--', 'tar', 'xpzf', f'/root/{driver}',
            '--strip-components=1', '-C', f'{nfs_root}/rootfs'
            ]

        self.run_command(extract_cmd, "Extract rootfs tarball")

        # Delete the driver tarball from the VM after extraction
        delete_cmd = ['lxc', 'exec', vm_name, '--', 'rm', '-f', f'/root/{driver}']
        self.run_command(delete_cmd, "Delete driver tarball after extraction")

        for action in [("restart", "Restart NFS server"), ("enable", "Enable NFS server")]:
            cmd = ["lxc", "exec", vm_name, "--", "sudo", "systemctl", action[0], "nfs-kernel-server"]
            self.run_command(cmd, action[1])

    def create_nfs_server_rpi(self, vm_name: str, nfs_root: str ,driver:str ,driver_path:str) -> None:
        """
        Configures the NFS server inside the VM.
        """
        vmcmd = ["lxc", "exec", vm_name, "--", "sudo"]
        vmcmd_no_sudo = ["lxc", "exec", vm_name, "--"]

        for folder in [nfs_root, f"{nfs_root}/rootfs"]:
            self.run_command(vmcmd + ["mkdir", folder],
                         f"Create folder {folder} in VM {vm_name}")
        
        self.run_command(vmcmd_no_sudo + ["chown", "-R", "nobody:nogroup", f"{nfs_root}"],
                         "Change ownership of NFS folder")
        self.run_command(vmcmd_no_sudo + ["sudo", "chmod", "755", f"{nfs_root}"],
                         "Set permissions for NFS folder")
        tarball_cmd = ['lxc', 'file', 'push', driver_path, f'{vm_name}/root/']
        self.run_command(tarball_cmd, "Push rootfs tarball")

        extract_cmd = [
        'lxc', 'exec', vm_name, '--', 'tar', '-xf', f'/root/{driver}',
        '--strip-components=1', '-C', f'{nfs_root}/rootfs'
        ]
        """extract_cmd = [
        'lxc', 'exec', vm_name, '--', 'tar', '-xf', f'/root/{driver}',
        '-C', f'{nfs_root}/'
        ]"""
        self.run_command(extract_cmd, "Extract rootfs tarball")

        # Delete the driver tarball from the VM after extraction
        delete_cmd = ['lxc', 'exec', vm_name, '--', 'rm', '-f', f'/root/{driver}']
        self.run_command(delete_cmd, "Delete driver tarball after extraction")

        """export_line = f"{nfs_root} " \
                  "*(rw,sync,no_subtree_check,no_root_squash,crossmnt)"
        self.run_command(
            ["lxc", "exec", vm_name, "--", "bash", "-c",
            f"echo '{export_line}' >> /etc/exports"],
            "Add NFS export to /etc/exports"
        )

        # NEW: exportfs -a (re‑load exports table)
        self.run_command(
            ["lxc", "exec", vm_name, "--", "sudo", "exportfs", "-a"],
            "Reload NFS exports
        )"""
         

        for action in [("restart", "Restart NFS server"), ("enable", "Enable NFS server")]:
            cmd = ["lxc", "exec", vm_name, "--", "sudo", "systemctl", action[0], "nfs-kernel-server"]
            self.run_command(cmd, action[1])

    def create_nfs_server_jtx2(self, vm_name: str, nfs_root: str ,driver:str ,driver_path:str) -> None:
        """
        Configures the NFS server inside the VM.
        """
        vmcmd = ["lxc", "exec", vm_name, "--", "sudo"]
        vmcmd_no_sudo = ["lxc", "exec", vm_name, "--"]

        for folder in [nfs_root, f"{nfs_root}/rootfs"]:
            self.run_command(vmcmd + ["mkdir", folder],
                         f"Create folder {folder} in VM {vm_name}")
        
        self.run_command(vmcmd_no_sudo + ["chown", "-R", "nobody:nogroup", f"{nfs_root}"],
                         "Change ownership of NFS folder")
        self.run_command(vmcmd_no_sudo + ["sudo", "chmod", "755", f"{nfs_root}"],
                         "Set permissions for NFS folder")
        tarball_cmd = ['lxc', 'file', 'push', driver_path, f'{vm_name}/root/']
        self.run_command(tarball_cmd, "Push rootfs tarball")

        extract_cmd = [
        'lxc', 'exec', vm_name, '--', 'tar', '-xf', f'/root/{driver}',
        '--strip-components=1', '-C', f'{nfs_root}/rootfs'
        ]
        """extract_cmd = [
        'lxc', 'exec', vm_name, '--', 'tar', '-xf', f'/root/{driver}',
        '-C', f'{nfs_root}/'
        ]"""
        self.run_command(extract_cmd, "Extract rootfs tarball")

        # Delete the driver tarball from the VM after extraction
        delete_cmd = ['lxc', 'exec', vm_name, '--', 'rm', '-f', f'/root/{driver}']
        self.run_command(delete_cmd, "Delete driver tarball after extraction")

        """export_line = f"{nfs_root} " \
                  "*(rw,sync,no_subtree_check,no_root_squash,crossmnt)"
        self.run_command(
            ["lxc", "exec", vm_name, "--", "bash", "-c",
            f"echo '{export_line}' >> /etc/exports"],
            "Add NFS export to /etc/exports"
        )

        # NEW: exportfs -a (re‑load exports table)
        self.run_command(
            ["lxc", "exec", vm_name, "--", "sudo", "exportfs", "-a"],
            "Reload NFS exports"
        )
         """

        for action in [("restart", "Restart NFS server"), ("enable", "Enable NFS server")]:
            cmd = ["lxc", "exec", vm_name, "--", "sudo", "systemctl", action[0], "nfs-kernel-server"]
            self.run_command(cmd, action[1])


    # --------------------------------------------------------------------------
    # 7. Additional Configuration
    # --------------------------------------------------------------------------
    def setup_vpn_vlan(self ,vpn_name, vlan):
        """Run the setup_eth_vlan_vpn.sh script with given VM name and VLAN."""
        try:
            subprocess.run([TOOLS_SCRIPT_PATH+"/setup_eth_vlan_vpn.sh", vpn_name, str(vlan)], check=True)
            print(f"Successfully configured VLAN {vlan} on VM {vpn_name}.")
        except subprocess.CalledProcessError as e:
            print(f"Error configuring VLAN {vlan} on VM {vpn_name}: {e}")


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
        
        """self.run_lxc_command(vm_name, ["mkdir", "-p", "/root/nbd_jetson"])
        logging.info("Created /root/nbd_jetson directory in VM %s", vm_name)
        self.run_lxc_command(vm_name, ["chmod", "755", "/root/nbd_jetson"])"""
 
    def _update_config_file(self, vm_name: str, nfs_server_ip: str, nodes: list) -> None:
        """
        Updates /etc/nbd-server/config by reading the current config and adding sections
        for any nodes that are missing. For each missing node:
        - Ensures the base image (/root/nbd_jetson.img) exists.
        - Creates a node-specific folder (/root/nbd_jetson_<node>).
        - Copies the base image into that folder (as nbd_jetson.img) if not already present.
        - Appends a configuration section for the node.
        """

        # Read the current configuration file.
        base_image_path = ""
        result = self.run_lxc_command(vm_name, ["cat", "/etc/nbd-server/config"])
        existing_config = result.stdout
     

        new_config_content = ""
        for node in nodes:

            if "j20" in node or "j40" or "jagx32" in node:
               base_image_path = BASE_IMAGE_J20_J40 
               base_image_name = NBD_IMAGE_NAME_J20_J40
            elif "j10"  in node:
                 base_image_path = BASE_IMAGE_J10
                 base_image_name = NBD_IMAGE_NAME_J10
            elif "jtx2" in node :
                 base_image_path = BASE_IMAGE_JTX
                 base_image_name = NBD_IMAGE_NAME_JTX

            node_section = f"[nbd_jetson_{node}]"
            # If the node section already exists, skip processing for this node.
            if node_section in existing_config:
                logging.info("Configuration for nbd %s already exists.", node)
                continue
    
            # Create the node-specific folder under /root.
            node_folder = f"/root/nbd_jetson_{node}"
            self.run_lxc_command(vm_name, ["mkdir", "-p", node_folder])
            
            # Define the node image path.
            node_image_path = f"{node_folder}/{base_image_name}"
            push_command = ["lxc", "file", "push", base_image_path, f"{vm_name}{node_image_path}"]
            self.run_command(push_command,"push nbd images ")
            
            # Append the node-specific configuration.
            new_config_content += f"[nbd_jetson_{node}]\n"
            new_config_content += f"exportname = {node_image_path}\n"
            new_config_content += "readonly = false\n"
            new_config_content += f"listenaddr = {nfs_server_ip}\n\n"

            # Append new sections to the configuration file if any.
            if new_config_content:
                self.run_lxc_command(vm_name, ["sh", "-c", f"echo '{new_config_content}' >> /etc/nbd-server/config"])


    def _update_config_file_1(self, vm_name: str, nfs_server_ip: str, nodes: list) -> None:
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
        dd_cmd = ["dd", "if=/dev/zero", f"of={image_path}", "bs=1M", f"count={NBD_SIZE}"]
        self.run_lxc_command(vm_name, dd_cmd)

        # Format the disk image as ext4.
        self.run_lxc_command(vm_name, ["mkfs.ext4", image_path])

    def _restart_nbd_server(self, vm_name: str) -> None:
        """
        Restarts the nbd-server service to apply the new configuration.
        """
        self.run_lxc_command(vm_name, ["systemctl", "restart", "nbd-server"])

    def configure_nbd_on_lxc_vm_1(self, vm_name: str, nfs_server_ip: str, nodes: list) -> None:
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

    def configure_nbd_on_lxc_vm(self, vm_name: str, nfs_server_ip: str, nodes: list) -> None:
            """
            Configures nbprofile inside the LXC VM for the provided nodes.
            
            For each node:
            - Creates a folder named /root/nbd_jetson_<node>.
            - Copies a common base image (/root/nbd_jetson.img) into that folder as nbd_jetson.img.
            - Adds a configuration section for the node pointing to its node-specific image.
            
            The base image is created (using dd and formatted with mkfs.ext4) if it does not exist.
            """
            logging.info("Setting up nbprofile inside VM %s for nodes: %s", vm_name, nodes)
            

            
            # Update the configuration file with sections for nodes that are missing.
            self._update_config_file(vm_name, nfs_server_ip, nodes)

            # Restart nbd-server to apply changes.
            self._restart_nbd_server(vm_name)
            
            logging.info("nbprofile setup completed in VM %s", vm_name)


    def setup_tftp_server(self, vm_name: str)-> None:
        """
         Install and configure tftpd-hpa inside an LXC container.

        """
        self.run_lxc_command(vm_name, ["apt", "install", "-y", "tftpd-hpa"])
        base_dir = "/var/lib/tftpboot"
               #  Create tftpboot directory and set permission
        self.run_lxc_command(vm_name, ["mkdir", "-p", base_dir])
        self.run_lxc_command(vm_name, ["chown", "-R", "tftp:tftp", base_dir])
        self.run_lxc_command(vm_name, ["chmod", "-R", "755", base_dir])

        #  Write tftpd-hpa default config with the correct directory
        config_script = f"""
cat << 'EOF' > /etc/default/tftpd-hpa
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="{ base_dir }"
TFTP_ADDRESS=":69"
TFTP_OPTIONS="--secure"
EOF
"""
        self.run_lxc_command(vm_name, ["bash", "-c", config_script])

        #  Restart and enable the service
        self.run_lxc_command(vm_name, ["systemctl", "restart", "tftpd-hpa"])
        self.run_lxc_command(vm_name, ["systemctl", "enable", "tftpd-hpa"])
        logging.info(
            "tftpd-hpa and filesystem setup completed in LXC VM '%s",
            vm_name

        )
    
    def setup_tftp_for_rpi_lxc(self, vm_name: str, rpi_version: str) -> None:
        """
        Install and configure tftpd-hpa inside an LXC container for Raspberry Pi devices.
        """

        base_dir = "/var/lib/tftpboot"
       #  Create version-specific subdirectory
        version_dir = f"{base_dir}/{rpi_version}"

        # Check if version_dir already exists; if so, skip setup
        try:
            self.run_lxc_command(vm_name, ["bash", "-c", f"test -d '{version_dir}'"])
            logging.info(
                "TFTP setup skipped: version directory '%s' already exists in VM '%s'",
                version_dir, vm_name
            )
            return
        except subprocess.CalledProcessError:
            # Directory does not exist, continue setup
            pass
        #  Create tftpboot directory and set permission
        self.run_lxc_command(vm_name, ["mkdir", "-p", version_dir])
        self.run_lxc_command(vm_name, ["chown", "-R", "tftp:tftp", version_dir ])
        self.run_lxc_command(vm_name, ["chmod", "-R", "755", version_dir ])

        #  Download and extract the RPi filesystem tarball
        tarball_url = f"http://{DRIVER_SERVER_IP}/{rpi_version}.tar.gz"
        local_tar = f"/root/{rpi_version}.tar.gz"
        self.run_lxc_command(vm_name, ["wget", "-O", local_tar, tarball_url])
        self.run_lxc_command(vm_name, ["tar", "-xf", local_tar, "-C", base_dir])
                #  Restart and enable the service
        self.run_lxc_command(vm_name, ["systemctl", "restart", "tftpd-hpa"])
        self.run_lxc_command(vm_name, ["systemctl", "enable", "tftpd-hpa"])
        logging.info(
            "tftpd-hpa and filesystem setup completed in LXC VM '%s' for RPi version '%s'",
            vm_name,
            rpi_version
        )


    def setup_tftp_for_jtx2_lxc(self, vm_name: str) -> None:
        """
        Install and configure tftpd-hpa inside an LXC container for Jtx2 (Jetsons) devices.
        """

        base_dir = "/var/lib/tftpboot"
       #  Create version-specific subdirectory
        jt_dirctory =f"{base_dir}/t186"
        tftp_jtx2_directory = f"{jt_dirctory}/jp3274"


        # Check if version_dir already exists; if so, skip setup
        try:
            self.run_lxc_command(vm_name, ["bash", "-c", f"test -d '{tftp_jtx2_directory }'"])
            logging.info(
                "TFTP setup skipped: version directory '%s' already exists in VM '%s'",
                tftp_jtx2_directory , vm_name
            )
            return
        except subprocess.CalledProcessError:
            # Directory does not exist, continue setup
            pass

        self.run_lxc_command(vm_name, ["mkdir", "-p",  jt_dirctory])
        self.run_lxc_command(vm_name, ["chown", "-R", "tftp:tftp",  jt_dirctory])
        self.run_lxc_command(vm_name, ["chmod", "-R", "755",  jt_dirctory])
        self.run_lxc_command(vm_name, ["mkdir", "-p",   tftp_jtx2_directory])
        self.run_lxc_command(vm_name, ["chown", "-R", "tftp:tftp",   tftp_jtx2_directory])
        self.run_lxc_command(vm_name, ["chmod", "-R", "755",   tftp_jtx2_directory])


        #  Restart and enable the service
        self.run_lxc_command(vm_name, ["systemctl", "restart", "tftpd-hpa"])
        self.run_lxc_command(vm_name, ["systemctl", "enable", "tftpd-hpa"])

        #  Download and extract the RPi filesystem tarball
        image_url = f"http://{DRIVER_SERVER_IP}/jtx2/Image"
        tegra_url = f"http://{DRIVER_SERVER_IP}/jtx2/tegra186-p3636-0001-p3509-0000-a01.dtb"

        self.run_lxc_command(vm_name, ["wget", "-P",  tftp_jtx2_directory, image_url])
        self.run_lxc_command(vm_name, ["wget", "-P",  tftp_jtx2_directory, tegra_url])


        logging.info(
            "tftpd-hpa and filesystem setup completed in LXC VM '%s' for jetson JTX2",
            vm_name
        )


    def update_nbd_config(self, vm_name: str, nfs_server_ip: str, nodes: list) -> None:
                    # Update the configuration file with sections for nodes that are missing.
            logging.info("Setting up nbprofile inside VM %s for new nodes: %s", vm_name, nodes)
            self._update_config_file(vm_name, nfs_server_ip, nodes)
            
            # Restart nbd-server to apply changes.
            self._restart_nbd_server(vm_name)
            
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
        index_name = REDIS_USER_INDEX
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
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


    def push_files_to_vm(self, vm_name, nfs_root, user_script_path, nfs_ip_addr, user_script_path_jp):
        """
        Push multiple files to the VM and create necessary directories.

        Parameters:
        - vm_name: Name of the virtual machine.
        - nfs_root: The NFS root directory path (e.g., "/root/nfsroot/").
        - user_script_path: The local folder path where the scripts are stored.
        - nfs_ip_addr: IP address for network file system operations.
        - user_script_path_jp: Additional script path for Jetson files.
        """


        # === Folder Creation Directory (Used for Creating Folders) ===
        base_folder_creation_dir = f"{nfs_root}/rootfs/home/mmtc"

        # === File Pushing Directory (Used for Pushing Files) ===
        base_file_pushing_dir = f"{vm_name}{nfs_root}/rootfs/home/mmtc"

        # Ensure the main scripts directory exists (folder creation directory)
        scripts_root = f"{base_folder_creation_dir}/scripts"
        self.run_command(["lxc", "exec", vm_name, "--", "mkdir", "-p", scripts_root], "Ensuring scripts root directory exists")

        # Define corrected folder structure inside `/root/nfsroot/rootfs/home/mmtc/scripts/`
        directories = {
            "setup": f"{scripts_root}/setup",       # Jetson & library setup scripts + Dockerfile
            "network": f"{scripts_root}/network",   # Network configuration scripts
            "system": f"{scripts_root}/system",     # System maintenance scripts
            "fan": f"{scripts_root}/fan",           # Fan control scripts
        }

        # Ensure required subdirectories exist inside `/root/nfsroot/rootfs/home/mmtc/`
        for key, path in directories.items():
            self.run_command(["lxc", "exec", vm_name, "--", "mkdir", "-p", path], f"Creating {key} directory in VM")

        # Define files and their corresponding directories (for file pushing)
        files_to_push = [
            ("Dockerfile", "setup", "Push Dockerfile to setup directory"),
            ("lib_setup.sh", "setup", "Push Jetson setup script"),
            ("jetson_setup.sh", "setup", "Push Jetson setup script"),
            ("restart_services.sh", "system", "Push system restart script"),
            ("configure_PPP.sh", "network", "Push network configuration script"),
            ("fan_control.py", "fan", "Push fan control script")
        ]

        # Loop through each file and push it to the appropriate directory (file pushing directory)
        for file_name, folder, description in files_to_push:
            # Determine the correct file path
            if file_name in ["lib_setup.sh", "Dockerfile", "jetson_setup.sh"]:
                full_user_script_path = os.path.join(USER_SCRIPT_PATH,user_script_path_jp)
            else:
                full_user_script_path = user_script_path

            file_path = os.path.join(full_user_script_path, file_name)
            #target_dir = directories[folder].replace(base_folder_creation_dir, base_file_pushing_dir)
            target_dir = os.path.join( directories[folder].replace(base_folder_creation_dir, base_file_pushing_dir), file_name)


            # Build and execute the command to push the file
            push_command = ["lxc", "file", "push", file_path, target_dir]
            self.run_command(push_command, description)

        # Create a README in the VM after pushing all files
        VmManager.create_readme_in_vm_j20_j40(vm_name, nfs_ip_addr, nfs_root)
        VmManager.create_readme_in_vm_nano_jtx(vm_name, nfs_ip_addr, nfs_root)

        print("All files successfully pushed and organized in the VM.")


    # --------------------------------------------------------------------------
    # 9. Tool Installation
    # --------------------------------------------------------------------------
    def install_library(self, vm_name: str, nfs_ip_addr: str ) -> None:
        """
        Installs necessary libraries and scripts in the VM for iot  devices.
        """

        self.run_command(["lxc", "exec", vm_name, "--", "sudo", "apt", "update"], "Update apt")
        install_binutils = ["lxc", "exec", vm_name, "--", "apt", "install", "-y", "binutils"]
        self.run_lxc_command(vm_name, ["apt", "install", "bzip2"])
        self.run_command(install_binutils, "Install binutils")
        install_nfs = ["lxc", "exec", vm_name, "--", "sudo", "apt", "install", "-y", "nfs-kernel-server"]
        self.run_command(install_nfs, "Install NFS server")
        # install tftp sever 
        self.setup_tftp_server(vm_name)
        # 1. Push the CLI script
        push_5gmmtctool = ["lxc", "file", "push", os.path.join(USER_SCRIPT_PATH, "5gmmtctool"), f"{vm_name}/root/"]
        self.run_command(push_5gmmtctool, "Push 5gmmtctool")
        # 2. Push the README
        push_readme = ["lxc", "file", "push",os.path.join(USER_SCRIPT_PATH, "VM_README.txt"),f"{vm_name}/root/"]
        self.run_command(push_readme, "Push VM_README.txt")
        # Install required packages and prepare the environment.    
        self._install_nbd_packages(vm_name)
        current_config = "[generic]\nallowlist = true\n\n"
        self.run_lxc_command(
         vm_name, ["sh", "-c", f"echo '{current_config}' > /etc/nbd-server/config"])
        #self.add_torch_script(vm_name, "install_torch.sh")
        
    

            
    def configure_nfs_jetson(self ,vm_name: str, nfs_ip_addr: str ,nfs_root:str ,driver :str, user_script_path_jp :str,driver_path:str):
        if self.folder_exists(vm_name, nfs_root):
            print(f"Folder {nfs_root} already exists in  {vm_name}. Skipping configuration steps.")
            return
        self.create_nfs_server(vm_name, nfs_root,driver,driver_path)
        push_nfs_setup = ["lxc", "file", "push", os.path.join(USER_SCRIPT_PATH, JETSON_SETUP_NFS), f"{vm_name}/root/"]
        self.run_command(push_nfs_setup, "Push NFS setup script")
        self.push_files_to_vm(vm_name,nfs_root,USER_SCRIPT_PATH,nfs_ip_addr,user_script_path_jp)
        time.sleep(7)

    def configure_nfs_raspberry(self ,vm_name: str,nfs_root:str ,driver :str,driver_path:str):
        if self.folder_exists(vm_name, nfs_root):
            print(f"Folder {nfs_root} already exists in  {vm_name}. Skipping configuration steps.")
            return
        self.create_nfs_server_rpi(vm_name, nfs_root,driver,driver_path)
        push_nfs_setup = ["lxc", "file", "push", os.path.join(USER_SCRIPT_PATH, RPI4_SETUP_NFS), f"{vm_name}/root/"]
        self.run_command(push_nfs_setup, "Push NFS setup script")
        time.sleep(5)

    def configure_nfs_jtx2(self ,vm_name: str,nfs_ip_addr: str ,nfs_root:str ,driver :str,user_script_path_jp :str,driver_path:str):
        if self.folder_exists(vm_name, nfs_root):
            print(f"Folder {nfs_root} already exists in  {vm_name}. Skipping configuration steps.")
            return
        self.create_nfs_server_jtx2(vm_name, nfs_root,driver,driver_path)
        push_nfs_setup = ["lxc", "file", "push", os.path.join(USER_SCRIPT_PATH, RPI4_SETUP_NFS), f"{vm_name}/root/"]
        self.run_command(push_nfs_setup, "Push NFS setup script")
        self.push_files_to_vm(vm_name,nfs_root,USER_SCRIPT_PATH,nfs_ip_addr,user_script_path_jp)
        time.sleep(5)


    

    def install_5gmmtctool(self, vm_name: str, nfs_ip_addr: str) -> None:
        """
        Installs the 5gmmtctool and updates DHCP configuration.
        """
        ip = IpAddr()
        ip.update_dhcp_configuration(DHCP_CONFIG_FILE_PATH, nfs_ip_addr)
        push_cmd = ["lxc", "file", "push", DHCP_CONFIG_FILE_PATH, f"{vm_name}/root/"]
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

        script_path = "/root/"+JETSON_SETUP_NFS
        logging.info("Executing NFS  in VM with %s %s", nfsroot_v,device_names)
        # First argument is now the nfsroot_v, followed by the device names
        args = " ".join([nfsroot_v] + device_names)
        
        try:
            subprocess.run(["lxc", "exec", vm_name, "--", "chmod", "+x", script_path], check=True)
            logging.info("Executing NFS setup script in VM %s %s", vm_name ,nfsroot_v)
            subprocess.run(["lxc", "exec", vm_name, "--", "bash", "-c", f"{script_path} {args}"], check=True)
            logging.info("NFS setup script executed successfully in VM %s", vm_name)
        except subprocess.CalledProcessError as e:
            logging.error("Error executing NFS setup in VM %s: %s", vm_name, e)
            raise

    # --------------------------------------------------------------------------
    # 10. NFS rasspbery setup
    # --------------------------------------------------------------------------
    def setup_nfs_rpi(self, vm_name: str, nfs_version: str, device_names: list[str]) -> None:
        """
            Executes the NFS setup script for Raspberry Pi inside the specified VM.

            Args:
                vm_name (str): Name of the LXC container (VM).
                nfs_version (str): Version tag of the NFS root (e.g., "v2").
                device_names (list[str]): List of device identifiers (e.g., hostnames or MACs).

            Usage:
                setup_nfs_raspberry("my_vm", "v2", ["raspi-1", "raspi-2"])
            """
        if not vm_name or not nfs_version or not device_names:
            logging.error("Usage: setup_nfs_raspberry('<VM_NAME>', '<nfs_version>', ['device1', 'device2', ...])")
            return


        script_path = "/root/"+RPI4_SETUP_NFS
        args = " ".join([ nfs_version] + device_names)

        try:
            # Ensure script is executable
            subprocess.run(["lxc", "exec", vm_name, "--", "chmod", "+x", script_path], check=True)

            # Execute the script with arguments inside the VM
            logging.info("Executing Raspberry Pi NFS setup script in VM '%s' with NFS version '%s' and devices %s",
                        vm_name, nfs_version, device_names)

            subprocess.run(
                ["lxc", "exec", vm_name, "--", "bash", "-c", f"{script_path} {args}"],
                check=True
            )

            logging.info("NFS setup script executed successfully in VM '%s'", vm_name)

        except subprocess.CalledProcessError as e:
            logging.error("Error executing NFS setup in VM '%s': %s", vm_name, e)

    def setup_nfs_jtx2(self ,
        vm_name: str,
        nfs_version: str,
        device_names: list[str]
    ) -> None:
        """
        Executes the NFS setup script for JTX2 inside the specified LXC VM.

        Args:
            vm_name (str): Name of the LXC container.
            nfs_version (str): Version tag of the NFS root (e.g., "v2").
            device_names (List[str]): List of device identifiers.
            script_name (str): Name of the setup script (defaults to JTX2_SETUP_NFS).

        Logs an error and returns if any argument is missing or if execution fails.
        """
        if not vm_name or not nfs_version or not device_names:
            logging.error(
                "Usage: setup_nfs_jtx2('<VM_NAME>', '<nfs_version>', ['device1', 'device2', ...])"
            )
            return

        script_path = "/root/"+RPI4_SETUP_NFS
        args = [str(script_path), nfs_version] + device_names

        try:
            # Ensure script is executable
            subprocess.run(
                ["lxc", "exec", vm_name, "--", "chmod", "+x", str(script_path)],
                check=True
            )

            logging.info(
                "Executing JTX2 NFS setup script in VM '%s' with version '%s' on devices %s",
                vm_name, nfs_version, device_names
            )

            # Execute the script inside the VM
            subprocess.run(
                ["lxc", "exec", vm_name, "--", "bash", "-c", " ".join(args)],
                check=True
            )

            logging.info("NFS setup for JTX2 completed successfully in VM '%s'", vm_name)

        except subprocess.CalledProcessError as e:
            logging.error("Error during NFS setup for JTX2 in VM '%s': %s", vm_name, e)
        # --------------------------------------------------------------------------
    # 11. Utility: README Creation
    # --------------------------------------------------------------------------
    @staticmethod
    def create_readme_in_vm_j20_j40(vm_name: str, nfs_ip_addr: str, rootfs:str)  -> None:
        """
        Creates a README.md file inside the VM with setup instructions.
        """
    
        nfs_ip = nfs_ip_addr.split('/')[0]
        content = f"""
        
# Jetson Configuration and Maintenance Guide

# instruction for 	Jetson-Xavier-NX (j20)	 jetson-Orin_nx (j40)

## 1. Jetson Initial Setup

Run the initial setup script with your NFS IP:

./scripts/system/restart_services.sh {nfs_ip}

📌 Replace {nfs_ip} with your actual NFS IP.

when Restart the Jetson execute the same scripts.

### 2. run the docker container 
sudo docker run -it --rm --privileged -v "$(pwd):/workspace" --net host mmtc-docker

##  Install Required Libraries (Optional)

Install necessary libraries using:

./scripts/setup/lib_setup.sh

##  Network Configuration (Optional)

Configure network connectivity:

./scripts/network/configure_PPP.sh


##  Fan Control (Optional)

Manage Jetson fan speed:

./scripts/fan/fan_control.py

"""    
        touch_cmd = f'lxc exec {vm_name} -- bash -c "touch {rootfs}/rootfs/home/mmtc/README_j20_j40.md"'
        try:
            subprocess.run(touch_cmd, shell=True, check=True)
            logging.info("Created README_j20_j40.md in VM %s", vm_name)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to create README_j20_j40.md: %s", e)
            raise
        write_cmd = (
            f'lxc exec {vm_name} -- bash -c "cat > {rootfs}/rootfs/home/mmtc/README_j20_j40.md << \'EOF\'\n'
            f'{content}\nEOF"'
        )
        try:
            subprocess.run(write_cmd, shell=True, check=True)
            logging.info("Populated README_j20_j40.md in VM %s", vm_name)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to write to README_j20_j40.md: %s", e)
            raise
    @staticmethod
    def create_readme_in_vm_nano_jtx(vm_name: str, nfs_ip_addr: str, rootfs:str)  -> None:
        """
        Creates a README.md file inside the VM with setup instructions.
        """
    
        nfs_ip = nfs_ip_addr.split('/')[0]
        content = f"""
        
# Jetson Configuration  and Maintenance Guide

# instruction for Jetson-Nano  (j10) Jetson-TX2-NX  (jtx2)

## 1.Install Required Libraries 

Install necessary libraries using:

./scripts/setup/lib_setup.sh

## 2. Jetson Initial Setup

Run the initial setup script with your NFS IP and hostname:

./scripts/setup/jetson_setup.sh {nfs_ip} jtx-2 or j10-1

📌 Replace {nfs_ip} with your actual NFS IP.

when Restart the Jetson execute the same scripts.

### 3. run the docker container  if not already run 
sudo docker run -it --rm --privileged -v "$(pwd):/workspace" --net host mmtc-docker

### restart process 
Run the initial setup script with your NFS IP:

./scripts/system/restart_services.sh {nfs_ip}

##  Network Configuration (Optional)

Configure network connectivity:

./scripts/network/configure_PPP.sh


##  Fan Control (Optional)

Manage Jetson fan speed:

./scripts/fan/fan_control.py

"""    
        touch_cmd = f'lxc exec {vm_name} -- bash -c "touch {rootfs}/rootfs/home/mmtc/README_j10_jtx.md"'
        try:
            subprocess.run(touch_cmd, shell=True, check=True)
            logging.info("Created README_j10_jtx.md in VM %s", vm_name)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to create README_j10_jtx.md: %s", e)
            raise
        write_cmd = (
            f'lxc exec {vm_name} -- bash -c "cat > {rootfs}/rootfs/home/mmtc/README_j10_jtx.md << \'EOF\'\n'
            f'{content}\nEOF"'
        )
        try:
            subprocess.run(write_cmd, shell=True, check=True)
            logging.info("Populated README_j10_jtx.md in VM %s", vm_name)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to write to README_j10_jtx.md: %s", e)
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
#vm_manager.setup_nfs_jetson("mtestvm","nfsroot-jp-3541",["j20-tribe4"])
#base_image_path="nbd_jetson.img"
#push_command = ["lxc", "file", "push", base_image_path, "mehdi/root/nbd_jetson_j20-tribe2/"]
#vm_manager.run_command(push_command,"push ")
#vm_manager.push_files_to_vm(vm_name="mehdi",nfs_root='/root/nfsroot-jp-3274',user_script_path=USER_SCRIPT_PATH , nfs_ip_addr="10.111.67.4",user_script_path_jp="jetson/jp3274/")
#vm_manager.create_readme_in_vm("mehdi",  nfs_ip_addr="10.111.67.4", rootfs='/root/nfsroot-jp-3274')
#ip = IpAddr()
#ip.update_dhcp_configuration(DHCP_CONFIG_FILE_PATH,"10.111.100.6/24")
"""push_nfs_setup = ["lxc", "file", "push", os.path.join(USER_SCRIPT_PATH, RPI4_SETUP_NFS), f"{"mehdi"}/root/"]
VmManager.run_command(push_nfs_setup, "Push NFS setup script")"""
#vm_manager.setup_nfs_rpi("mehdi","nfsroot_rpi4",['rpi4-3'])
#vm_manager.create_nfs_server_rpi("mehdi","/root/nfsroot_rpi4","core-image-minimal-rpi4-rootfs.tar.bz2","../config/core-image-minimal-rpi4-rootfs.tar.bz2")