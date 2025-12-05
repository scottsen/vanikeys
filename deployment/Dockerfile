# VaniKeys RunPod Serverless Dockerfile
#
# This image contains VaniKeys with RunPod SDK for serverless GPU deployment
#
# Base image: RunPod's PyTorch image with CUDA support
# Size: ~8GB (includes PyTorch, CUDA libraries)

FROM docker.io/runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel

WORKDIR /workspace

# Copy VaniKeys source code
COPY . /workspace/vanikeys

# Install VaniKeys dependencies
RUN cd /workspace/vanikeys && \
    pip install --no-cache-dir -e .

# Install RunPod SDK
RUN pip install --no-cache-dir runpod

# Copy handler
COPY deployment/runpod_handler.py /workspace/

# Verify installation
RUN python -c "import vanikeys; from vanikeys.crypto import generate_master_seed; from vanikeys.matchers import MultiSubstringMatcher; print('VaniKeys import successful')"

# RunPod expects the handler to be at the root
CMD ["python", "-u", "/workspace/runpod_handler.py"]

# Metadata
LABEL org.opencontainers.image.title="VaniKeys RunPod Handler"
LABEL org.opencontainers.image.description="Serverless GPU handler for VaniKeys vanity SSH key generation"
LABEL org.opencontainers.image.version="0.2.0"
LABEL org.opencontainers.image.authors="Scott Senger <scottsen@tia.net>"
