#!/bin/bash
# ----------------------------------------------------------
# Script: install_nvidia_docker.sh
# Purpose: Update system packages, install necessary tools,
#          libraries, and set up nvidia-docker2.
#
# Steps:
#   • Update package lists and fix broken dependencies.
#   • Install basic tools and additional libraries.
#   • Install NVIDIA container runtime.
#   • Check for nvidia-container-toolkit installation.
#   • Configure repository and install nvidia-docker2.
# ----------------------------------------------------------

# 1. Update system and install tools and libraries
echo "Updating package lists and installing required tools and libraries..."
sudo apt update -qq
sudo apt --fix-broken install -y

# Install basic tools and additional packages
sudo apt install -y curl gnupg vim ppp

# Install additional libraries
sudo apt install -y libopenblas-dev
sudo apt install -y libcublas-11-4 cuda-toolkit-11-4 nvidia-cudnn8 
sudo apt install -y libjpeg-dev libpng-dev

# Install NVIDIA container runtime
sudo apt-get install -y nvidia-container-runtime

# Verify if nvidia-container-toolkit is installed
echo "Verifying NVIDIA container toolkit installation..."
dpkg -l | grep nvidia-container-toolkit

# 2. Install nvidia-docker2
echo "Installing nvidia-docker2..."
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get install -y nvidia-docker2

echo "Installation complete."
