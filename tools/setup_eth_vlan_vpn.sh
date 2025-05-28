#!/bin/bash
set -e

# Usage: ./setup_eth_vlan_vpn.sh <vm_name> <vlan>
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <vm_name> <vlan>"
  exit 1
fi

vm_name="$1"
vlan="$2"
device_name="vpn_vlan${vlan}"
parent_interface="eno1"

# Validate that the parent interface exists on the host
if ! ip link show "$parent_interface" &>/dev/null; then
  echo "Error: Parent interface $parent_interface does not exist. Please check your network configuration."
  exit 1
fi

# Check if the device already exists in the VM configuration
existing_devices=$(sudo lxc config device list "$vm_name")
if echo "$existing_devices" | grep -q "$device_name"; then
  echo "Device '$device_name' already exists on VM '$vm_name'. Nothing to do."
  exit 0
  #echo "Device $device_name already exists on $vm_name. Removing it..."
  #sudo lxc config device remove "$vm_name" "$device_name"
fi

# Add macvlan device to VM
echo "Adding macvlan device '$device_name' to VM $vm_name with VLAN $vlan..."
sudo lxc config device add "$vm_name" "$device_name" nic \
  nictype=macvlan \
  parent="$parent_interface" \
  vlan="$vlan"


# Wait for interface to appear in the VM
echo "Waiting for new interface to appear inside the VM..."
sleep 5  # Give it time to initialize

# Identify and select the best candidate interface
iface=""
for i in {1..50}; do
  candidate_iface="eth$i"

  # skip if the interface doesn't exist at all
  if ! sudo lxc exec "$vm_name" -- ip link show "$candidate_iface" &>/dev/null; then
    continue
  fi
  iface_status=$(sudo lxc exec "$vm_name" -- ip link show "$candidate_iface" 2>/dev/null | grep -q "UP" && echo "UP" || echo "DOWN")
  ip_address=$(sudo lxc exec "$vm_name" -- ip -4 addr show "$candidate_iface" 2>/dev/null | grep -oP '(?<=inet\s)\d+\.\d+\.\d+\.\d+(/\d+)?' || echo "None")
  
  echo "Interface: $candidate_iface - Status: $iface_status - IP: $ip_address"
  
  # Select the first available DOWN interface without an IP
  if [ "$iface_status" == "DOWN" ] || [ "$ip_address" == "None" ]; then
    iface="$candidate_iface"
    echo "Selected interface: $iface"
    break
  fi
done

if [ -z "$iface" ]; then
  echo "Error: No available network interface detected inside the VM. Exiting."
  exit 1
fi

# Compute the guest IP inside the VM
guest_ip="10.111.${vlan}.30/24"

# Configure the network interface inside the VM
echo "Configuring IP address ${guest_ip} on interface ${iface} inside VM $vm_name..."
sudo lxc exec "$vm_name" -- bash -c "ip addr add ${guest_ip} dev ${iface} && ip link set dev ${iface} up"

# Add iptables NAT rule to allow outbound traffic
echo "Adding iptables NAT rule on the VM for interface ${iface}..."
sudo lxc exec "$vm_name" -- bash -c "iptables -t nat -A POSTROUTING -o ${iface} -j MASQUERADE"

echo "Setup complete using device $device_name on interface ${iface}."