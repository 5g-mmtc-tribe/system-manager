

## Architecture and Configuration (from code)


### User VMs/Containers

The command lines below summarized how the VMs are configured in different places of the code (as 7 aug 2024)

```
lxc launch ubuntu:<ubuntu_version> <vm_name> --vm --device root,size=<root_size> -c limits.cpu=4 -c limits.memory=4GiB

sudo ip link add <macvlan_name> link <interface_name> type macvlan mode bridge
sudo ip link set dev <macvlan_name> up
sudo ip addr add <ip_addr> dev <macvlan_name>

lxc config device add <vm_name> eth1 nic nictype=macvlan parent=<macvlan_name>
```

/etc/netplan/50-cloud-init.yaml is:
```
# network: {config: disabled}
network:
    version: 2
    ethernets:
        enp5s0:
            dhcp4: true
        enp6s0:
            dhcp4: no
            addresses:
              - 192.168.0.227/24
```

```
lxc exec <vm_name> -- sudo sh -c "echo 'network: {config: disabled}' > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg"
lxc exec <vm_name> -- sudo netplan apply
```

TODO: is missing to get NAT in the VMs
```
iptables -t nat -A POSTROUTING -o enp5s0 -j MASQUERADE
```

## Architecture and Configuration (from Chetanveer's report), maybe be updated

### Default Configuration:

- The lxd init command creates a default bridge named lxdbr0.
- Each container is connected to this bridge through Virtual Ethernet pairs (veth pairs),
establishing layer 2 connectivity.
- The bridge serves as the default gateway for the containers, allowing them to access the
internet.
- LXD updates the host’s routing table to include a route from the physical internet connec-
tion to the default gateway (lxdbr0).

### Routing Configuration:
- LXD updates the host’s routing table as part of the configuration process.
- The routing table on the host is modified to include a route to the default gateway, which
is lxdbr0.
- This ensures that communication from containers to the internet is routed through the
lxdbr0 bridge.

### User Isolation with LXD Profiles:
- Users are isolated by the creation of LXD profiles, with each user assigned a specific profile.
- These profiles act as a means of containment, preventing communication between containers
associated with different profiles.
- Isolating users in this manner enhances security by limiting interaction between containers,
maintaining a controlled environment.

