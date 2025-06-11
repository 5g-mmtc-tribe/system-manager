VM QUICK-START GUIDE
====================

This short guide shows how to discover IP addresses, reach your VM and
embedded boards over SSH, and restart the key services that keep the lab
network running.

----------------------------------------------------------------------
1. Show the VM’s IP address on interface “enp6s0”
----------------------------------------------------------------------

    python3 ./5gmmtctool get-vm-ip
      → enp6s0: 192.168.10.23

Once you have the address, connect to the VM itself:

    ssh root@<VM_IP>

----------------------------------------------------------------------
2. List current DHCP leases (who got what IP)
----------------------------------------------------------------------

    python3 ./5gmmtctool  list-dhcp-leases
    IP              MAC               HOST                 EXPIRES (UTC)
    192.168.10.11   aa:bb:cc:dd:ee:ff jetson-orin          2025-06-04 12:52:00

• After flashing a Jetson-Nano or Jetson-Xavier-NX, the board requests an
  address from the VM’s isc-dhcp-server—check it here.

• Jetson-TX2-NX and Raspberry Pi images are flashed automatically,
  so their first boot also shows up in this list.

----------------------------------------------------------------------
3. SSH access to the devices
----------------------------------------------------------------------

First, make sure your public key is present on the VM
(usually in /root/.ssh/authorized_keys).

Then connect:

  • Jetson-Nano / Jetson-TX2-NX / Jetson-Xavier-NX
        ssh mmtc@<DEVICE_IP>
        password: tribe

  • Raspberry Pi
        ssh -oHostKeyAlgorithms=+ssh-rsa \
            -oPubkeyAcceptedAlgorithms=+ssh-rsa \
            root@10.111.113.6
        (first login as root; you may add user “mmtc” later)

----------------------------------------------------------------------
4. Restart both NFS and DHCP services
----------------------------------------------------------------------

    sudo ./5gmmtctool.py restart-services

Run this whenever you modify /etc/exports or /etc/dhcp/dhcpd.conf so
changes take effect immediately.

----------------------------------------------------------------------
