#!/bin/bash
set -e

# Check for required command-line argument for the NBD server IP.
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <NBD_server_IP>"
  exit 1
fi

nbd_server_ip="$1"

# Get the hostname and set workspace and docker data-root based on it
HOSTNAME=$(hostname)
workspace_dir="/mnt/Workspace_${HOSTNAME}"
docker_data_root="${workspace_dir}/var-lib/docker"
echo "=== Installing and Configuring NBD-Client ==="
sudo apt update -qq
sudo apt install -y nbd-client

# Remove and reinstall to ensure a proper service file is in place
sudo rm -f /lib/systemd/system/nbd-client.service

#sudo apt-get install --reinstall -y nbd-client
sudo systemctl daemon-reload
sleep 2
sudo systemctl restart nbd-client
sudo systemctl enable nbd-client

# Connect to NBD server using the command-line supplied IP
echo "Connecting to NBD server at ${nbd_server_ip}   nbd_jetson_"${HOSTNAME}"  ... "
sudo nbd-client -d /dev/nbd0
sudo nbd-client "${nbd_server_ip}" 10809 /dev/nbd0 -name nbd_jetson_"${HOSTNAME}"

# Format and mount the NBD device to the workspace
echo "Formatting /dev/nbd0 with ext4..."
sudo mkfs.ext4  -F /dev/nbd0
echo "Mounting /dev/nbd0 to ${workspace_dir}..."
sudo mount /dev/nbd0 "$workspace_dir"
echo "=== Restarting Docker service ==="
sudo systemctl restart docker
sudo systemctl enable docker


echo "=== Handling Docker Image ==="

if [ -f mmtc-docker.tar ]; then
  # Load image from tar file if it exists.
  echo "Docker tar file found. Loading Docker image..."
  sudo docker load -i mmtc-docker.tar
elif [ -f Dockerfile ]; then
  # Build image from Dockerfile if tar file is missing.
  echo "No Docker tar file found. Dockerfile detected. Building Docker image 'mmtc-docker'..."
  sudo docker build -t mmtc-docker .
else
  echo "No Docker image tar file or Dockerfile found. Skipping Docker container run."
  exit 1
fi

echo "Running Docker container..."
sudo docker run -it --rm --privileged -v "$(pwd):/workspace" --net host mmtc-docker

echo "Jetson setup completed successfully!"