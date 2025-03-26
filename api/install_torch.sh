#!/bin/bash
# install update 
sudo apt update
# Install python3-pip and libopenblas-dev
sudo apt-get -y install python3-pip libopenblas-dev

# Install Torch
export TORCH_INSTALL=http://developer.download.nvidia.cn/compute/redist/jp/v512/pytorch/torch-2.1.0a0+41361538.nv23.06-cp38-cp38-linux_aarch64.whl
python3 -m pip install --no-cache $TORCH_INSTALL

# Install libcublas-11-4
sudo apt install -y libcublas-11-4

# Install cuda-toolkit-11-4
sudo apt-get install -y cuda-toolkit-11-4

# Install nvidia-cudnn8
sudo apt install -y nvidia-cudnn8
