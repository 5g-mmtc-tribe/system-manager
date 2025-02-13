#!/bin/bash

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
  if [ ! -f "$file" ]; then
    echo "Configuring file: $file"
    # The file needs to be configured with the following content
    echo '{
      "runtimes": {
        "nvidia": {
          "path": "nvidia-container-runtime",
          "runtimeArgs": []
        }
      },
      "default-runtime": "nvidia",
      "data-root": "/mnt/Workspace/var-lib/docker"
    }' | sudo tee "$file" > /dev/null
  else
    echo "File already configured: $file"
  fi
}

# 1. Install necessary tools
echo "Updating and installing required tools..."
sudo apt update -qq
sudo apt --fix-broken install -y
sudo apt install -y curl gnupg vim
sudo apt-get install -y nvidia-container-runtime

# 2. Install nvidia-docker2
echo "Installing nvidia-docker2..."
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get install -y nvidia-docker2

# 3. Check if Docker daemon is configured (if not, configure it)
docker_daemon_config="/etc/docker/daemon.json"
configure_file_if_not_exists "$docker_daemon_config"

# 4. Configure Workspace folder
echo "Setting up Workspace folder..."

workspace_dir="/mnt/Workspace"
create_dir_if_not_exists "$workspace_dir"

# Set ownership for Workspace
echo "Setting ownership for Workspace..."
sudo chown -R $(whoami):$(whoami) /mnt/Workspace

# Create tmp directory and set permissions
create_dir_if_not_exists "/mnt/Workspace/tmp"
echo "Setting permissions for /mnt/Workspace/tmp..."
sudo chmod 1777 /mnt/Workspace/tmp

# Export TMPDIR
echo "Exporting TMPDIR..."
export TMPDIR=/mnt/Workspace/tmp

# Create var-lib-docker directory and symlink it
create_dir_if_not_exists "/mnt/Workspace/var-lib/docker"
echo "Creating symlink for /var/lib/docker..."
sudo ln -s /mnt/Workspace/var-lib/docker /var/lib/docker

# 5. Restart Docker and enable it to start on boot
echo "Restarting Docker service..."
sudo systemctl restart docker
sudo systemctl enable docker

echo "Jetson setup completed successfully!"
