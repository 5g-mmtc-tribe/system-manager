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

sudo systemctl daemon-reload
sleep 2
echo "=== Installing and Configuring NBD-Client ==="
sudo apt update -qq
sudo apt install -y nbd-client

# Remove and reinstall to ensure a proper service file is in place
sudo rm -f /lib/systemd/system/nbd-client.service
sleep 2
#sudo apt-get install --reinstall -y nbd-client
sudo systemctl restart nbd-client
sudo systemctl enable nbd-client
# Connect to NBD server using the command-line supplied IP
echo "Connecting to NBD server at ${nbd_server_ip}..."
sudo nbd-client "${nbd_server_ip}" 10809 /dev/nbd0 -name nbd_jetson

# Format and mount the NBD device to the workspace
echo "Formatting /dev/nbd0 with ext4..."
sudo mkfs.ext4 /dev/nbd0
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


echo "=== Building and Running Docker Container (Optional) ==="
# If a Dockerfile exists in the current directory, build and run the container.
if [ -f Dockerfile ]; then
  echo "Dockerfile found. Building Docker image 'mmtc-docker'..."
  sudo docker build -t mmtc-docker .
  echo "Running Docker container 'mmtc-docker'..."
  sudo docker run -it --rm --privileged -v "$(pwd)":" --net host mmtc-docker
else
  echo "No Dockerfile found. Skipping Docker image build and run."
fi

echo "Jetson setup completed successfully!"

