#!/bin/bash
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

