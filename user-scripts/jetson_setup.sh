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

# Function to check if a directory exists and create it if it doesn't
create_dir_if_not_exists() {
  dir=$1
  if [ ! -d "$dir" ]; then
    echo "Creating directory: $dir"
    sudo mkdir -p "$dir"
  else
    echo "Directory already exists: $dir"
  fi
}

# Function to check if a file exists and configure it if needed
configure_file_if_not_exists() {
  file=$1
  echo "docker configuration file: $file"

  sudo tee "$file" > /dev/null <<EOF
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "default-runtime": "nvidia",
  "data-root": "$docker_data_root"
}
EOF
}

echo "=== Configuring Docker daemon ==="
docker_daemon_config="/etc/docker/daemon.json"
configure_file_if_not_exists "$docker_daemon_config"

echo "=== Setting up Workspace folder based on hostname ==="
create_dir_if_not_exists "$workspace_dir"

# Set ownership for Workspace
echo "Setting ownership for Workspace at $workspace_dir..."
sudo chown -R "$(whoami)":"$(whoami)" "$workspace_dir"

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

# Create tmp directory and set permissions inside the workspace folder
create_dir_if_not_exists "${workspace_dir}/tmp"
echo "Setting permissions for ${workspace_dir}/tmp..."
sudo chmod 1777 "${workspace_dir}/tmp"

# Export TMPDIR
echo "Exporting TMPDIR to ${workspace_dir}/tmp..."
export TMPDIR="${workspace_dir}/tmp"

# Create docker data-root directory and create a symlink to /var/lib/docker
create_dir_if_not_exists "$docker_data_root"
if [ ! -L /var/lib/docker ]; then
  echo "Creating symlink for Docker data-root..."
  sudo ln -s "$docker_data_root" /var/lib/docker
else
  echo "Docker symlink already exists: /var/lib/docker"
fi

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