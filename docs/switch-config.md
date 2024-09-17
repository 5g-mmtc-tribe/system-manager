# Network Configuration Guide

## Switch Configuration

1. **Set the Enable Secret and Passwords:**

    ```plaintext
    enable secret pass: {enable_secret}
    password remote {remote_password}
    hostname {hostname}
    ```

2. **Configure VLAN 1:**

    ```plaintext
    interface vlan 1
    ip address {ip_address} {subnet_mask}
    no shutdown
    ```

3. **Enable Telnet Access:**

    ```plaintext
    line vty 0 15
    password {vty_password}
    login
    transport input telnet
    ```

## Server Configuration

1. **Modify Network Interface Name:**

    Create or edit the udev rules file to assign a new name to the network interface. Use the following command to open the file:

    ```bash
    sudo nano /etc/udev/rules.d/70-persistent-net.rules
    ```

    Add the following line, replacing `{MAC_ADDRESS}` with the actual MAC address of the network interface and `{newname}` with your desired name:

    ```plaintext
    SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="{MAC_ADDRESS}", NAME="{newname}"
    ```

    Save and close the file.

2. **Apply Changes:**

    Reload udev rules to apply the new interface name:

    ```bash
    sudo udevadm control --reload-rules
    ```

    Reboot or restart the network service to see the changes take effect.

3. **Set a Static IP Address for the Server:**

    Configure the static IP address for the server interface `{interface}` using the `ip` command:

    ```bash
    sudo ip addr add {static_ip}/24 dev {interface}
    ```

    To make this change persistent across reboots, you'll need to update the network configuration file for your distribution. For example, on a system using NetworkManager, you would modify the appropriate connection file or use `nmcli` to set the IP address.
