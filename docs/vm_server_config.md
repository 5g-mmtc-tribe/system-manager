
# Virtual Machine and Server Setup

## 1. Virtual Machine Setup (VM Side)

### 1.1 Launch Ubuntu VM with LXC
```bash
lxc launch ubuntu:24.04 <vmName> --vm --device root,size=<diskSize GB> -c limits.cpu=4 -c limits.memory=4GiB
```

### 1.2 Set Up Macvlan VLAN
```bash
lxc config device add <vmName> eth2 nic nictype=macvlan parent=<serverInterface> vlan=<vlanID>
ip addr add <vmVlanAddress> dev enp7s0
ip link set enp7s0 up
```

### 1.3 Configure Netplan with NFS IP Address
Edit the Netplan configuration:
```bash
sudo vi /etc/netplan/50-cloud-init.yaml
```
Add the following content:
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

### 1.4 Set Up NFS Root
```bash
sudo apt install nfs-kernel-server
sudo mkdir /root/nfsroot_<jetpack_version>
sudo chown -R nobody:nogroup /root/nfsroot_<jetpack_version>
sudo chmod 755 /root/nfsroot_<jetpack_version>
```

### 1.5 Configure NFS Export
```bash
sudo lxc exec <vm-name> -- bash -c 'echo "/root/nfsroot_<jetpack_version> *(async,rw,no_root_squash,no_all_squash,no_subtree_check,insecure,anonuid=1000,anongid=1000,crossmnt)" >> /etc/exports'
sudo exportfs -a
sudo systemctl restart nfs-kernel-server
sudo systemctl enable nfs-kernel-server
sudo apt install binutils
```

### 1.6 Configure NBD
1. **Install and set up NBD-Server:**
   ```bash
   sudo apt install -y nbd-server
   sudo mkdir -p /root/nbd_jetson
   sudo chmod 755 /root/nbd_jetson
   ```
2. **Edit NBD configuration:**
   ```bash
   sudo vi /etc/nbd-server/config

   [generic]
      allowlist = true
      #   #includedir = /etc/nbd-server/conf.d

   # setup Jetson Xavier / Jetson Orin
   [nbd_jetson]
      exportname = /root/nbd_jetson/nbd_jetson.img
      readonly = false
      listenaddr = <ip vm server>

   # setup Jetson Nano
   [nbd_jetson_jp3274]
      exportname = /root/nbd_jetson_jp3274/nbd_jetson_jp3274.img
      readonly = false
      listenaddr = <ip vm server>
   ```

3. **Create images for NBD:**
   ```bash
   sudo dd if=/dev/zero of=/root/nbd_jetson/nbd_jetson.img bs=1M count=4096     # Jetson Nano
   sudo dd if=/dev/zero of=/root/nbd_jetson/nbd_jetson.img bs=1M count=13312   # Jetson Xavier / Jetson Orin
   sudo mkfs.ext4 /root/nbd_jetson/nbd_jetson.img                              # Jetson Xavier / Jetson Orin
   sudo mkfs.ext4 /root/nbd_jetson_jp3274/nbd_jetson_jp3274.img                # Jetson Nano
   ```

4. **(Optional) Download NBD images with Docker inside:**
   ```bash
   # _Jetson Xavier / Jetson Orin_
   sudo wget -P nbd_jetson_{jetson_Name}/ http://193.55.250.147/nbd-images/nbd_jetson_jp3541.img
   ```

   ```bash
   # _Jetson Nano_
   sudo wget -P nbd_jetson_{jetson_Name} http://193.55.250.147/nbd-images/nbd_jetson_jp3274.img
   ```

### 1.7 Set Up DHCP Server
```bash
lxc exec <vmName> -- bash -c 'sudo cat /root/test.txt > /etc/dhcp/dhcpd.conf'
sudo apt install isc-dhcp-server
sudo vi /etc/dhcp/dhcpd.conf
```
Add the following:
```bash
subnet 192.168.0.0 netmask 255.255.255.0 {
  range 192.168.0.12 192.168.0.15;
  option routers 192.168.0.10;
  option domain-name-servers 8.8.8.8, 8.8.4.4;
}
```
Start and enable DHCP:
```bash
sudo systemctl restart isc-dhcp-server
sudo systemctl enable isc-dhcp-server
```

5. **Download and extract rootfs (example commands):**

   - **Jetson Xavier / Jetson Orin:**
     ```bash
     wget http://193.55.250.147/rootfs-jetson/rootfs-basic-jp3541-noeula-user.tar.gz
     sudo tar xpzf /root/rootfs-basic-jp3541-noeula-user.tar.gz -C /root/nfsroot-jp-3274/
     ```

   - **Jetson Nano:**
     ```bash
     wget http://193.55.250.147/rootfs-jetson/rootfs-jp3274.tar.gz
     sudo tar xpzf /root/rootfs-basic-jp3274-noeula-user.tar.gz -C /root/nfsroot-jp-3541/
     ```

---

## 2. Server Side Setup

1. **Install Necessary Tools:**

   ```bash
   # Jetson Xavier NX, Orin NX
   sudo apt-get install bzip2
   wget https://developer.nvidia.com/downloads/embedded/l4t/r35_release_v4.1/release/jetson_linux_r35.4.1_aarch64.tbz2
   ```

   ```bash
   # Jetson Nano 4GB
   wget https://developer.nvidia.com/downloads/embedded/l4t/r32_release_v7.4/t210/jetson-210_linux_r32.7.4_aarch64.tbz2
   wget https://developer.nvidia.com/downloads/embedded/l4t/r32_release_v7.4/t210/tegra_linux_sample-root-filesystem_r32.7.4_aarch64.tbz2
   ```

2. **Extract and Prepare Files:**

   - **Jetson Xavier NX / Orin NX:**
     ```bash
     sudo tar -xf jetson_linux_r35.4.1_aarch64.tbz2
     cd Linux_for_Tegra/
     sudo ./tools/samplefs/nv_build_samplefs.sh --abi aarch64 --distro ubuntu --flavor basic --version focal
     cd Linux_for_Tegra/rootfs/
     sudo tar xpf ../tools/samplefs/sample_fs.tbz2
     cd ..
     ```

   - **Jetson Nano 4GB:**
     ```bash
     sudo tar -xf jetson-210_linux_r32.7.4_aarch64.tbz2
     cd Linux_for_Tegra/rootfs/
     sudo tar xpf ../../tegra_linux_sample-root-filesystem_r32.7.4_aarch64.tbz2
     cd ..
     ```

3. **Apply Binaries:**
   ```bash
   sudo add-apt-repository universe
   sudo apt-get update
   sudo apt-get install qemu-user-static
   sudo ./apply_binaries.sh
   ```

4. **Create Default User (EULA Acceptance/User Configuration):**
   ```bash
   sudo apt-get install -y lz4 libxml2-utils
   sudo ./tools/l4t_create_default_user.sh -u mmtc -p tribe -n mmtc -a --accept-license
   ```

5. **Set Up Lighttpd Web Server:**
   ```bash
   sudo apt install lighttpd -y
   sudo systemctl start lighttpd
   sudo systemctl enable lighttpd
   sudo nano /etc/lighttpd/lighttpd.conf
   ```

6. **Save Driver Files:**
   - **Jetson Nano:**
     ```bash
     sudo tar czvf rootfs-jp3274.tar.gz rootfs/.
     sudo cp rootfs-noeula-user.tar.gz /var/www/html/
     ```
   - **Jetson Xavier / Jetson Orin:**
     ```bash
     sudo tar czvf rootfs-jp3541-basic-noeula-user.tar.gz rootfs/
     sudo cp rootfs-noeula-user.tar.gz /var/www/html/
     ```

7. **Flash the Device:**
   ```bash
   sudo ./flash.sh -N <nfsIP>:/root/nfsroot_<jetpack_version> --rcm-boot jetson-nano-emmc eth0          # Jetson Nano 4GB
   sudo ./flash.sh -N <nfsIP>:/root/nfsroot_<jetpack_version> --rcm-boot jetson-xavier-nx-devkit eth0   # Jetson Xavier NX
   sudo ./flash.sh -N <nfsIP>:/root/nfsroot_<jetpack_version> --rcm-boot jetson-orin-nano-devkit eth0   # Jetson Orin NX
   ```

---

## 3. Jetson Setup

### 3.1 Enable NAT and Internet Access
```bash
ip route del default via <gatewayIP>
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

### 3.2 Install Diverse Tools
- **Jetson Xavier / Jetson Orin**:
  ```bash
  sudo apt update -qq
  sudo apt --fix-broken install -y
  sudo apt install -y curl gnupg vim ppp
  sudo apt install -y libopenblas-dev
  sudo apt install -y libcublas-11-4 cuda-toolkit-11-4 nvidia-cudnn8
  sudo apt install -y libjpeg-dev libpng-dev
  sudo apt-get install -y nvidia-container-runtime
  dpkg -l | grep nvidia-container-toolkit
  distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
  curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
  curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
  sudo apt-get install -y nvidia-docker2
  ```

- **Jetson Nano**:
  ```bash
  sudo apt update -qq
  sudo apt --fix-broken install -y
  sudo apt install -y curl gnupg vim ppp
  sudo apt install -y libopenblas-dev
  sudo apt install -y libcublas-dev cuda-toolkit-10-2 nvidia-cudnn8
  sudo apt install -y libjpeg-dev libpng-dev
  sudo apt-get install -y nvidia-container-runtime
  dpkg -l | grep nvidia-container-toolkit
  distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
  curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
  curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
  sudo apt-get install -y nvidia-docker2
  ```

### 3.3 Configure Docker Daemon
```bash
sudo vi /etc/docker/daemon.json

{
   "runtimes": {
      "nvidia": {
         "path": "nvidia-container-runtime",
         "runtimeArgs": []
      }
   },
   "default-runtime": "nvidia",
   "data-root": "/mnt/Workspace/var-lib/docker"
}
```

### 3.4 Docker Container
- **Jetson Xavier / Jetson Orin**:
  ```bash
  #======= jetson container DockerHub =======
  FROM dustynv/l4t-pytorch:r35.4.1
  ENV DEBIAN_FRONTEND=noninteractive

  RUN apt-get update && apt-get install -y --no-install-recommends \
      && apt-get clean && rm -rf /var/lib/apt/lists/*

  RUN python3 -m pip install --upgrade pip

  RUN pip install --no-cache-dir \
      protobuf onnx pycuda \
      torchvision==0.15.1 torchaudio==2.0.1 numpy matplotlib \
      setuptools packaging wheel psutil jsonrpcclient jsonrpcserver \
      msgpack msgpack-numpy \
      grpcio grpcio-tools

  WORKDIR /workspace

  CMD ["/bin/bash"]
  ```

- **Jetson Nano**:
  ```bash
  #======= jetson container DockerHub =======
  FROM dustynv/l4t-pytorch:r32.7.1
  ENV DEBIAN_FRONTEND=noninteractive

  RUN apt-get update && apt-get install -y --no-install-recommends \
      && apt-get clean && rm -rf /var/lib/apt/lists/*

  RUN python3 -m pip install --upgrade pip

  RUN pip install --no-cache-dir \
      protobuf onnx pycuda \
      numpy matplotlib \
      setuptools packaging wheel psutil jsonrpcclient jsonrpcserver \
      msgpack msgpack-numpy \
      grpcio grpcio-tools

  WORKDIR /workspace

  CMD ["/bin/bash"]
  ```

### 3.5 Configure PPP Modem
(Based on “Data over UART with PPP User Guide Cloud Sequans”)
```bash
sudo vi /etc/ppp/options
```
```
/dev/ttyUSB2
115200
nodetach
noauth
local
noipdefault
defaultroute
usepeerdns
crtscts
lock
debug
dump
-chap
connect "/usr/sbin/chat -t6 -f /etc/chatscripts/connect"
disconnect "/usr/sbin/chat -t6 -f /etc/chatscripts/disconnect"
```
```bash
sudo vi /etc/chatscripts/connect
```
```
#ABORT "NO CARRIER"
TIMEOUT 30
ABORT ERROR
"" AT
OK AT+CFUN=1
OK AT+CGDATA="PPP",1
CONNECT ""
```
```bash
sudo vi /etc/chatscripts/disconnect
```
```
"" "\d\d\d+++\c"
```

### 3.6 Install NBD-client
```bash
sudo apt update -qq
sudo apt install -y nbd-client
sudo systemctl daemon-reload
sudo systemctl restart nbd-client
sudo systemctl enable nbd-client
```

### 3.7 Connect to NBD-server
```bash
sudo mkdir -p /mnt/Workspace
sudo chown -R $(whoami):$(whoami) /mnt/Workspace
sudo nbd-client <nfsIP> 10809 /dev/nbd0 -name nbd_jetson
sudo mkfs.ext4 /dev/nbd0
sudo mount /dev/nbd0 /mnt/Workspace
```

### 3.8 Configure Workspace Folder
```bash
sudo mkdir -p /mnt/Workspace/tmp
sudo chmod 1777 /mnt/Workspace/tmp
export TMPDIR=/mnt/Workspace/tmp
sudo mkdir -p /mnt/Workspace/var-lib/docker
sudo ln -s /mnt/Workspace/var-lib/docker /var/lib/docker
sudo systemctl restart docker
sudo systemctl enable docker
```

### 3.9 Build Dockerfile
```bash
mkdir Workspace
vi Dockerfile      # Paste the Dockerfile content here
sudo docker build -t mmtc-docker .
# Wait for build to finish
sudo docker run -it --rm --privileged -v $(pwd):/workspace --net host mmtc-docker
```

### 3.10 Fan Control
(Based on [fan-control](https://github.com/piyoki/fan-control/tree/master))
```bash
#!/usr/bin/env python3
import time

#==============file paths================
TEMP_SENSOR = "/sys/class/thermal/thermal_zone1/temp"
TARGET_PWM = "/sys/devices/tegra-cache/subsystem/devices/pwm-fan/hwmon/hwmon4/pwm1"

#=======Reads temperature from the sensor file and returns it in °C.=======
def read_temperature():
    try:
        with open(TEMP_SENSOR, "r") as f:
            temp_str = f.read().strip()
        return int(temp_str) / 1000.0  # Convert to °C
    except Exception as e:
        print("Error reading temperature:", e)
        return None

#=======Capture PWM value to the fan control routine.=======
def set_fan_speed(pwm_value):
    try:
        with open(TARGET_PWM, "w") as f:
            f.write(str(pwm_value))
    except Exception as e:
        print("Error setting fan speed:", e)

#=======fan mode and PWM value based on the temperature.=======
def determine_fan_settings(temperature):
    if temperature < 40:
        mode = 0
        pwm = 80
    elif 40 <= temperature < 60:
        mode = 1
        pwm = 150
    else:
        mode = 2
        pwm = 255
    return mode, pwm

def main():
    while True:
        temperature = read_temperature()
        if temperature is None:
            time.sleep(10)
            continue

        mode, pwm = determine_fan_settings(temperature)
        print(f"Current temp: {temperature:.2f}°C, Fan mode: {mode}, PWM: {pwm}")
        set_fan_speed(pwm)
        time.sleep(10)  # Adjust interval as needed

if __name__ == "__main__":
    main()
```

---

## 4. OpenVPN Setup

Below is an example for creating a separate VM `vm-openvpn` for OpenVPN.

```bash
lxc launch ubuntu:24.04 vm-openvpn --vm --device root,size=20GB -c limits.cpu=4 -c limits.memory=4GiB
```

### 4.1 Install OpenVPN and Easy-RSA
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install openvpn easy-rsa -y
```

### 4.2 Set Up CA and Server Certificates
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
*(Password phrase: “admin” or “iotlab”)*

### 4.3 Configure the OpenVPN Server
Copy certificate files and create a server configuration:
```bash
sudo cp pki/ca.crt pki/issued/server.crt pki/private/server.key pki/dh.pem ta.key /etc/openvpn/
sudo nano /etc/openvpn/server.conf
```
Example configuration:
```bash
local 10.71.241.150
port 1194
proto tcp
dev tun
auth-user-pass-verify /etc/openvpn/auth_sqlite.sh via-file
script-security 3
#plugin /usr/lib/openvpn/openvpn-plugin-auth-pam.so openvpn
ca /etc/openvpn/ca.crt
cert /etc/openvpn/server.crt
key /etc/openvpn/server.key
dh /etc/openvpn/dh.pem
tls-auth /etc/openvpn/ta.key 0
server 10.8.0.0 255.255.255.0

#define the vlan ip address
# vlan 1
push "route 10.111.67.0 255.255.255.0"
# vlan 2
push "route 10.111.212.0 255.255.255.0"
#define the  webportal network
push "route 10.71.241.184 255.255.255.255"
#api access
push "route 192.168.0.8 255.255.255.255"
#push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 8.8.8.8"
push "dhcp-option DNS 8.8.4.4"
keepalive 10 120
cipher AES-256-CBC
auth SHA256
status /var/log/openvpn-status.log
log-append /var/log/openvpn.log
verb 3
```
Then:
```bash
sudo systemctl restart openvpn
```

### 4.4 Port Forwarding for the VPN Server
```bash
iptables -t nat -A PREROUTING -p tcp --dport 2220 -j DNAT --to-destination 10.71.241.150:1194
iptables -A FORWARD -p tcp -d 10.71.241.150 --dport 2220 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT
```

### 4.5 Enable IP Forwarding
```bash
sudo nano /etc/sysctl.conf
sudo iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
```

### 4.6 Create Client Configuration
```bash
./easyrsa gen-req minig nopass
./easyrsa sign-req client testcl
```
Create the `.ovpn` file:
```bash
cat <<EOF > /root/openvpn-ca/mehdi.ovpn
client
dev tun
proto tcp
remote 193.55.250.147 2220
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
auth-user-pass
#route 10.111.67.4 255.255.255.255
#route-nopull
<ca>
$(cat /etc/openvpn/ca.crt)
</ca>
<cert>
$(cat /root/openvpn-ca/pki/issued/mehdi.crt)
</cert>
<key>
$(cat /root/openvpn-ca/pki/private/mehdi.key)
</key>
<tls-auth>
$(cat /etc/openvpn/ta.key)
</tls-auth>
EOF

sudo cp /etc/openvpn/ta.key #copy tls-auth key
sudo openvpn --config <clientName>.ovpn
```

### 4.7 Add VLAN Client Interface
```bash
lxc config device add vm-openvpn-server eth195 nic nictype=macvlan parent=eno1 vlan=195
ip addr add 10.111.195.30/24 dev enp6s0
sudo ip link set dev eth1 up
sudo iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE
```

---

## Annex

### A.1 Check IP Tables NAT
```bash
sudo iptables -t nat -L -n -v
```

### A.2 Add Public Key
```bash
sudo lxc file push -r <sourceFile> <vmName>/<destinationPath>
ssh-copy-id -i ~/.ssh
```
```bash
# To make this permanent, run on vpn 
sysctl -w net.ipv4.ip_forward=1
sudo openvpn --config /etc/openvpn/server.conf
```

---