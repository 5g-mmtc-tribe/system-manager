#!/bin/bash
# ----------------------------------------------------------
# Script: install_nvidia_docker.sh
# Purpose: Install and configure NVIDIA Docker environment
#          along with necessary dependencies.
#
# Steps:
#   1. Update package lists and fix broken dependencies.
#   2. Install essential system tools and libraries.
#   3. Install NVIDIA container runtime.
#   4. Install nvidia-docker2.
#   5. Verify installation.
# ----------------------------------------------------------

set -e  # Exit on error

echo "Updating package lists and fixing broken dependencies..."
sudo apt update -qq
sudo apt --fix-broken install -y

echo "Installing essential tools and libraries..."
sudo apt install -y curl gnupg vim ppp libopenblas-dev \
                    libcublas-dev cuda-toolkit-10-2 nvidia-cudnn8 \
                    libjpeg-dev libpng-dev

echo "Installing NVIDIA container runtime..."
sudo apt-get install -y nvidia-container-runtime

echo "Checking NVIDIA container toolkit installation..."
dpkg -l | grep nvidia-container-toolkit || echo "NVIDIA container toolkit is not installed!"

echo "Configuring NVIDIA Docker repository..."
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

echo "Installing nvidia-docker2..."
sudo apt-get update -qq
sudo apt-get install -y nvidia-docker2

echo "Installation complete. You may need to restart the Docker service:"
echo "sudo systemctl restart docker"
