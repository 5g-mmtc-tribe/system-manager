
---

# Virtual Machine and Server Setup

## Virtual Machine Setup (VM Side)

### 1. Launch Ubuntu VM with LXC

```bash
lxc launch ubuntu:24.04 <vmName> --vm --device root,size=<diskSize GB> -c limits.cpu=4 -c limits.memory=4GiB
```

### 2. Set Up Macvlan VLAN

```bash
lxc config device add <vmName> eth2 nic nictype=macvlan parent=<serverInterface> vlan=<vlanID>
ip addr add <vmVlanAddress> dev enp7s0
ip link set enp7s0 up
```

### 3. Configure Netplan with NFS IP Address

Edit the Netplan configuration:

```bash
sudo vi /etc/netplan/50-cloud-init.yaml
```

Add the following:

```yaml
network:
  version: 2
  ethernets:
    enp5s0:
      dhcp4: true    
    enp6s0:
      dhcp4: no
      addresses:
        - <nfsAddress>/24
```

### 4. Set Up NFS Root

```bash
sudo apt install nfs-kernel-server
sudo mkdir /nfsroot
sudo chown -R nobody:nogroup /nfsroot
sudo chmod 755 /nfsroot
```

### 5. Set Up Lighttpd Web Server

```bash
sudo apt install lighttpd -y
sudo systemctl start lighttpd
sudo systemctl enable lighttpd
sudo nano /etc/lighttpd/lighttpd.conf
```

Download and extract the root filesystem:

```bash
wget http://193.55.250.148/rootfs-noeula-user.tar.gz
sudo tar xpzf /root/rootfs-noeula-user.tar.gz -C /root/nfsroot/
```

### 6. Configure NFS Export

```bash
sudo lxc exec <vmName> -- bash -c 'echo "/nfsroot *(async,rw,no_root_squash,no_all_squash,no_subtree_check,insecure,anonuid=1000,anongid=1000)" >> /etc/exports'
sudo exportfs -a
sudo systemctl restart nfs-kernel-server
sudo systemctl enable nfs-kernel-server
sudo apt install binutils
```

### 7. Set Up DHCP Server

```bash
lxc exec <vmName> -- bash -c 'sudo cat /root/test.txt > /etc/dhcp/dhcpd.conf'
sudo apt install isc-dhcp-server
sudo vi /etc/dhcp/dhcpd.conf
```

Add the following configuration:

```bash
subnet <subnetAddress> netmask <netmask> {
  range <rangeStart> <rangeEnd>;
  option routers <gatewayAddress>;
  option domain-name-servers <dns1>, <dns2>;
}
```

Start and enable the DHCP service:

```bash
sudo systemctl restart isc-dhcp-server
sudo systemctl enable isc-dhcp-server
```

## Server Side Setup

### 1. Install Necessary Tools

```bash
sudo apt-get install bzip2
wget https://developer.nvidia.com/downloads/embedded/l4t/r35_release_v4.1/release/jetson_linux_r35.4.1_aarch64.tbz2
wget https://developer.nvidia.com/downloads/embedded/l4t/r35_release_v4.1/release/tegra_linux_sample-root-filesystem_r35.4.1_aarch64.tbz2
```

### 2. Extract and Prepare Files

```bash
sudo tar -xf jetson_linux_r35.4.1_aarch64.tbz2
cd Linux_for_Tegra/rootfs/
sudo tar xpf ../../tegra_linux_sample-root-filesystem_r35.4.1_aarch64.tbz2
cd ..
```

### 3. Apply Binaries

```bash
sudo add-apt-repository universe
sudo apt-get update
sudo apt-get install qemu-user-static
sudo ./apply_binaries.sh
```

### 4. Create Default User (EULA Acceptance)

```bash
sudo apt-get install -y lz4 libxml2-utils
sudo ./tools/l4t_create_default_user.sh -u <username> -p <password> -n <hostname> --accept-license
```

### 5. Save Driver Files

```bash
sudo tar czvf rootfs-noeula-user.tar.gz rootfs/
sudo cp rootfs-noeula-user.tar.gz /var/www/html/
```

### 6. Flash the Device

```bash
sudo ./flash.sh -N <nfsIP> --rcm-boot <jetsonDevice> eth0
```

## Jetson Setup

### 1. Enable NAT and Internet Access

```bash
ip route del default via <gatewayIP>
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o enp5s0 -j MASQUERADE
```

### 2. Install PyTorch

```bash
sudo apt-get -y install python3-pip libopenblas-dev
export TORCH_INSTALL=http://developer.download.nvidia.cn/compute/redist/jp/v512/pytorch/torch-2.1.0a0+41361538.nv23.06-cp38-cp38-linux_aarch64.whl
python3 -m pip install --no-cache $TORCH_INSTALL
sudo apt install libcublas-11-4 cuda-toolkit-11-4 nvidia-cudnn8
chmod +x install_torch.sh
```

## OpenVPN Setup

### 1. Install OpenVPN and Easy-RSA

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install openvpn easy-rsa -y
```

### 2. Set Up CA and Server Certificates

```bash
make-cadir ~/openvpn-ca
cd ~/openvpn-ca
./easyrsa init-pki
./easyrsa build-ca
./easyrsa gen-req server nopass
./easyrsa sign-req server server
./easyrsa gen-dh
openvpn --genkey --secret ta.key
```

### 3. Configure the OpenVPN Server

Copy certificate files and create a server configuration:

```bash
sudo cp pki/ca.crt pki/issued/server.crt pki/private/server.key pki/dh.pem ta.key /etc/openvpn/
sudo nano /etc/openvpn/server.conf
```

Add the following configuration:

```bash
port 1194
proto tcp
dev tun
ca /etc/openvpn/ca.crt
cert /etc/openvpn/server.crt
key /etc/openvpn/server.key
dh /etc/openvpn/dh.pem
tls-auth /etc/openvpn/ta.key 0
server 10.8.0.0 255.255.255.0
#define the  webportal network 
push "10.154.195.235 255.255.255.255"
#define the vlan ip address 
push "10.111.106.0 255.255.255.0"
#push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 8.8.8.8
push "dhcp-option DNS 8.8.8.4
keepalive 10 120
cipher AES-256-CBC
auth SHA256
status /var/log/openvpn-status.log
log-append /var/log/openvpn.log
verb 3
```

### 4. Enable IP Forwarding

```bash
sudo nano /etc/sysctl.conf
```

### 5. Create Client Configuration

```bash
./easyrsa gen-req <clientName> nopass
./easyrsa sign-req client <clientName>
```

Create the client `.ovpn` file:

```bash
cat <<EOF > /root/openvpn-ca/tribe.ovpn
client
dev tun
proto tcp
remote 10.154.195.130  1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
data-ciphers AES-256-GCM:AES-256-CBC
data-ciphers-fallback AES-256-CBC
auth SHA256
key-direction 1
verb 3
mssfix 1300
keepalive 10 60
route-nopull
<ca>
$(cat /etc/openvpn/ca.crt)
</ca>
<cert>
$(cat /root/openvpn-ca/pki/issued/tribe.crt)
</cert>
<key>
$(cat /root/openvpn-ca/pki/private/tribe.key)
</key>
EOF
sudo cp /etc/openvpn/ta.key #copy tls-auth key 

sudo openvpn --config <clientName>.ovpn
```

### 6. OpenVPN VLAN Configuration

```bash
lxc config device add <vpnVM> eth130 nic nictype=macvlan parent=<serverInterface> vlan=<vlanID>
ip addr add <vpnVlanAddress>/24 dev <vpnInterface>
sudo ip link set dev <vpnInterface> up
sudo iptables -t nat -A POSTROUTING -o <vpninterface> -j MASQUERADE
socat TCP-LISTEN:1194,fork TCP:10.154.195.130:1194 &
```

---

## Annex

### 1. Check IP Tables NAT

```bash
sudo iptables -t nat -L -n -v
```

### 2. Add Public Key

```bash
sudo lxc file push -r <sourceFile> <vmName>/<destinationPath>
ssh-copy-id -i ~/.ssh
