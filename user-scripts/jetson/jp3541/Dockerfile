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