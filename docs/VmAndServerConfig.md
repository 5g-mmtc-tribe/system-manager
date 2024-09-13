
---

# Virtual Machine and Server Setup

## Virtual Machine Setup (VM Side)

### 1. Launch Ubuntu VM with LXC

```bash
lxc launch ubuntu:24.04 mehdivm --vm --device root,size=40GiB -c limits.cpu=4 -c limits.memory=4GiB
```

### 2. Set Up Macvlan

```bash
sudo ip link add <macvlan_name> link eno3 type macvlan mode bridge
sudo ip link set <macvlan_name> up
sudo ip addr add <macvlan_ip>/24 dev <macvlan_name>
lxc config device add mehdivm eth1 nic nictype=macvlan parent=<macvlan_name>
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
        - 192.168.0.10/24
```

### 4. Set Up NFS Root

```bash
sudo apt install nfs-kernel-server
sudo mkdir /nfsroot
sudo chown -R nobody:nogroup /nfsroot
sudo chmod 755 /nfsroot
```

Copy the necessary files:

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

Configure the NFS export:

```bash
sudo lxc exec mehdivm -- bash -c 'echo "/nfsroot *(async,rw,no_root_squash,no_all_squash,no_subtree_check,insecure,anonuid=1000,anongid=1000)" >> /etc/exports'
sudo exportfs -a
sudo systemctl restart nfs-kernel-server
sudo systemctl enable nfs-kernel-server
sudo apt install binutils
```

### 5. Set Up DHCP Server

```bash
lxc exec mehdivm -- bash -c 'sudo cat /root/test.txt > /etc/dhcp/dhcpd.conf'
sudo apt install isc-dhcp-server
sudo vi /etc/dhcp/dhcpd.conf
```

Add the following configuration:

```bash
subnet 192.168.0.0 netmask 255.255.255.0 {
  range 192.168.0.12 192.168.0.15;
  option routers 192.168.0.10;
  option domain-name-servers 8.8.8.8, 8.8.4.4;
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
sudo ./tools/l4t_create_default_user.sh -u iotuser -p iotuser -n iotuser --accept-license
```

### 5. Save Driver Files

```bash
sudo tar czvf rootfs-noeula-user.tar.gz rootfs/
sudo cp rootfs-noeula-user.tar.gz /var/www/html/
```

### 6. Flash the Device

```bash
sudo ./flash.sh -N <nfsIP> --rcm-boot jetson-xavier-nx-devkit-emmc eth0
```

## Jetson Setup

### 1. Enable NAT and Internet Access

```bash
ip route del default via 192.168.55.100
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
proto udp
dev tun
ca /etc/openvpn/ca.crt
cert /etc/openvpn/server.crt
key /etc/openvpn/server.key
dh /etc/openvpn/dh.pem
tls-auth /etc/openvpn/ta.key 0
server 10.8.0.0 255.255.255.0
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 8.8.8.8"
push "dhcp-option DNS 8.8.4.4"
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
./easyrsa gen-req debbah nopass
./easyrsa sign-req client debbah
```

Create the client `.ovpn` file:

```bash
cat <<EOF > /root/openvpn-ca/debbah.ovpn
client
dev tun
proto tcp
remote 193.55.250.147 2221
route 10.111.150.0 255.255.255.0
route 10.29.50.0 255.255.255.0
route 10.8.0.0 255.255.255.0
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
$(cat /root/openvpn-ca/pki/issued/debbah.crt)
</cert>
<key>
$(cat /root/openvpn-ca/pki/private/debbah.key)
</key>
EOF
sudo openvpn --config debbah.ovpn
```

## Annex

### 1. Check IP Tables NAT

```bash
sudo iptables -t nat -L -n -v
```

### 2. Add Public Key

```bash
sudo lxc file push -r jetson/Linux_for_Tegra/rootfs-noeula.tar.gz mehdivm/root/nfsroot
ssh-copy-id -i ~/.ssh/id_rsa.pub root@10.29.50