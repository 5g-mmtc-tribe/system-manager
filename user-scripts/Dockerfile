# Use a base image compatible with Jetson
FROM nvcr.io/nvidia/l4t-base:35.4.1

# Set environment for non-interactive installs
ENV DEBIAN_FRONTEND=noninteractive
ARG OPENCV_VERSION=4.5.5
ARG OPENCV_FOLDER=/workspace/opencv_build

# Define CUDA and NVIDIA versions
ENV CUDA_VERSION=11.4
ENV TORCH_INSTALL=https://developer.download.nvidia.com/compute/redist/jp/v511/pytorch/torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl
ENV PATH="/usr/local/cuda-${CUDA_VERSION}/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda-${CUDA_VERSION}/lib64:/usr/lib/aarch64-linux-gnu:/usr/local/cuda/targets/aarch64-linux/lib:${LD_LIBRARY_PATH}"

# Add NVIDIA Jetson repositories
RUN echo "deb https://repo.download.nvidia.com/jetson/common r35.5 main" > /etc/apt/sources.list.d/nvidia-l4t-apt-source.list && \
    echo "deb https://repo.download.nvidia.com/jetson/t234 r35.5 main" >> /etc/apt/sources.list.d/nvidia-l4t-apt-source.list && \
    echo "deb https://repo.download.nvidia.com/jetson/ffmpeg r35.5 main" >> /etc/apt/sources.list.d/nvidia-l4t-apt-source.list && \
    apt-get -qq update

# Install system dependencies (without unneeded dependencies like `libopencv-dev`)
RUN apt-get install -y --no-install-recommends \
    build-essential cmake git curl unzip \
    libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    python2.7-dev python3-dev python3-numpy \
    libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libdc1394-22-dev \
    libv4l-dev v4l-utils qv4l2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install CUDA, cuDNN, and TensorRT
RUN apt-get -qq update && apt-get install -y --no-install-recommends \
    cuda-toolkit-${CUDA_VERSION} \
    nvidia-cuda nvidia-cuda-dev nvidia-cudnn8 nvidia-cudnn8-dev \
    nvidia-tensorrt nvidia-tensorrt-dev libcublas-dev-${CUDA_VERSION} && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python and dependencies
RUN apt-get -qq update && apt-get install -y --no-install-recommends \
    python3 python3-pip libopenblas-dev && \
    python3 -m pip install --upgrade pip && \
    pip install --no-cache-dir $TORCH_INSTALL && \
    pip install --no-cache-dir \
        protobuf==3.20.3 onnx pycuda \
        torchvision==0.15.1 torchaudio==2.0.1 numpy matplotlib \
        setuptools packaging wheel psutil jsonrpcclient jsonrpcserver \
        msgpack msgpack-numpy && \
    rm -rf /var/lib/apt/lists/*

# Build OpenCV from source
#RUN mkdir -p ${OPENCV_FOLDER} && cd ${OPENCV_FOLDER} && \
#    curl -L https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip -o opencv.zip && \
#    curl -L https://github.com/opencv/opencv_contrib/archive/${OPENCV_VERSION}.zip -o opencv_contrib.zip && \
#    unzip opencv.zip && unzip opencv_contrib.zip && \
#    mkdir -p opencv-${OPENCV_VERSION}/build && cd opencv-${OPENCV_VERSION}/build && \
#    cmake -D CMAKE_BUILD_TYPE=RELEASE \
#          -D CMAKE_INSTALL_PREFIX=/usr/local \
#          -D WITH_CUDA=ON \
#          -D WITH_CUDNN=ON \
#          -D CUDA_ARCH_BIN="5.3,6.2,7.2" \
#          -D CUDA_ARCH_PTX="" \
#          -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib-${OPENCV_VERSION}/modules \
#          -D WITH_GSTREAMER=ON \
#          -D WITH_LIBV4L=ON \
#          -D BUILD_opencv_python2=ON \
#          -D BUILD_opencv_python3=ON \
#          -D BUILD_TESTS=OFF \
#          -D BUILD_PERF_TESTS=OFF \
#          -D BUILD_EXAMPLES=OFF .. && \
#    make -j$(nproc) && \
#    make install && \
#    ldconfig && \
#    rm -rf ${OPENCV_FOLDER}

RUN apt-get -qq update && apt-get install -y --no-install-recommends \
    libopencv-dev python3-opencv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]