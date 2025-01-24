# Network Configuration Guide

## Switch Configuration init 

### 1. Set the Enable Secret and Passwords

```plaintext
enable secret pass: {enable_secret}
password remote {remote_password}
hostname {hostname}
```

### 2. Configure VLAN 1

Set up VLAN 1 with a default IP address of `192.168.0.30`:

```plaintext
interface vlan 1
ip address 192.168.0.30 255.255.255.0
no shutdown
switchport mode trunk
```

> Replace `192.168.0.30` with a custom IP address if needed.

### 3. Enable Telnet Access

```plaintext
line vty 0 15
password {vty_password}
login
transport input telnet
```

---
## switch advanced setting 
## Enabling SSH on the Switch

### Step 1: Configure Basic Settings

Set the hostname, domain name, and clock:

```plaintext
Switch> enable
Switch# configure terminal
Switch(config)# hostname MySwitch
MySwitch(config)# ip domain-name mydomain.com
MySwitch(config)# clock set 12:00:00 1 April 2022
```

- Replace `MySwitch` with your desired hostname.
- Replace `mydomain.com` with your domain name.
- Adjust the date and time to your requirements.

---

### Step 2: Configure User Authentication

Create a local user account with privileged access for SSH:

```plaintext
MySwitch(config)# username myuser privilege 15 secret mypassword
```

- Replace `myuser` with your desired username.
- Replace `mypassword` with your desired password.

---

### Step 3: Generate RSA Keys

Generate an RSA keypair for secure SSH access:

```plaintext
MySwitch(config)# crypto key generate rsa general-keys modulus 2048
```

- The `modulus 2048` parameter specifies a 2048-bit key. For enhanced security, 2048 bits are recommended.

---

### Step 4: Enable SSH Version 2

Enable SSH Version 2 for better security:

```plaintext
MySwitch(config)# ip ssh version 2
```

---

### Step 5: Configure SSH Access on VTY Lines

Set SSH as the allowed protocol on all VTY lines and enable local authentication:

```plaintext
MySwitch(config)# line vty 0 15
MySwitch(config-line)# transport input ssh
MySwitch(config-line)# login local
MySwitch(config-line)# exit
```

---

### Step 6: Save Your Configuration

Save your configuration to ensure it persists across reboots:

```plaintext
MySwitch# write memory
```

---

### Testing Your SSH Connection

Once SSH is configured, test your connection using an SSH client. Connect to the switch using the IP address assigned to VLAN 1 (default: `192.168.0.30`):

```bash
ssh myuser@192.168.0.30
```

---

## Server Configuration

### 1. Modify Network Interface Name

To rename a network interface:

1. Open the udev rules file:

    ```bash
    sudo nano /etc/udev/rules.d/70-persistent-net.rules
    ```

2. Add the following line, replacing `{MAC_ADDRESS}` with the actual MAC address and `{newname}` with the desired name:

    ```plaintext
    SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="{MAC_ADDRESS}", NAME="{newname}"
    ```

3. Save and close the file.

### 2. Apply Changes

1. Reload udev rules:

    ```bash
    sudo udevadm control --reload-rules
    ```

2. Reboot the system or restart the network service for changes to take effect.

### 3. Set a Static IP Address for the Server

1. Assign a static IP address to the interface `{interface}` using the `ip` command:

    ```bash
    sudo ip addr add {static_ip}/24 dev {interface}
    ```

2. To make this change persistent across reboots, update the appropriate network configuration file for your system. For systems using NetworkManager, modify the connection file or use `nmcli` to configure the static IP address.

---

## SSH Troubleshooting

### Problem 1: Unable to Negotiate Key Exchange Method

**Error:**  
`Unable to negotiate with xxxx port 22: no matching key exchange method found. Their offer: diffie-hellman-group1-sha1,diffie-hellman-group14-sha1`

**Solution:**  
Edit your SSH configuration file:

1. Open the SSH config file:

    ```bash
    vim ~/.ssh/config
    ```

2. Add the following lines:

    ```plaintext
    Host *
        KexAlgorithms +diffie-hellman-group1-sha1,diffie-hellman-group14-sha1
    ```

3. Save and exit the file.

---

### Problem 2: No Matching Host Key Type Found

**Error:**  
`no matching host key type found. their offer: ssh-rsa`

**Solution:**  
Edit your SSH configuration file:

1. Open the SSH config file:

    ```bash
    vim ~/.ssh/config
    ```

2. Add the following lines:

    ```plaintext
    Host * 
        PubkeyAcceptedAlgorithms +ssh-rsa 
        HostKeyAlgorithms +ssh-rsa
    ```

3. Save and exit the file.

