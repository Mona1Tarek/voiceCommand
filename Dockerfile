# Build stage
FROM ubuntu:22.04 AS builder

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install build dependencies including libzmq3-dev for pyzmq
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev build-essential \
    libzmq3-dev \
    libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev \
    pulseaudio-utils pulseaudio \
    alsa-utils wget unzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Install Python dependencies globally
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install scipy
RUN pip3 install pyzmq

# Copy the source code
COPY src /build/src

# Create directory for ONNX models
RUN mkdir -p /build/onnx-models/all-MiniLM-L6-v2-onnx

# Attempt to download the ONNX model
RUN wget --tries=2 --timeout=10 -O /build/onnx-models/all-MiniLM-L6-v2-onnx/model.onnx \
    https://huggingface.co/onnx-models/all-MiniLM-L6-v2-onnx/resolve/main/model.onnx || \
    wget --tries=2 --timeout=10 -O /build/onnx-models/all-MiniLM-L6-v2-onnx/model.onnx \
    https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/model.onnx || \
    (echo "Warning: Failed to download ONNX model.")

# Create directory for VOSK model
RUN mkdir -p /build/vosk-model-small-en-us
RUN wget --tries=2 --timeout=10 -O /build/vosk-model-small-en-us/vosk-model-small-en-us-0.15.zip \
    https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && \
    unzip /build/vosk-model-small-en-us/vosk-model-small-en-us-0.15.zip -d /build/vosk-model-small-en-us/temp && \
    mv /build/vosk-model-small-en-us/temp/vosk-model-small-en-us-0.15/* /build/vosk-model-small-en-us/ && \
    rm -r /build/vosk-model-small-en-us/temp && \
    rm /build/vosk-model-small-en-us/vosk-model-small-en-us-0.15.zip

# Final stage
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    libasound-dev libportaudio2 libportaudiocpp0 \
    pulseaudio-utils pulseaudio \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy everything installed in builder
COPY --from=builder /usr/local /usr/local

# Force reinstall pyzmq directly in final stage
RUN pip3 install --force-reinstall pyzmq

# Set working directory
WORKDIR /app

# Copy the required models
COPY --from=builder /build/vosk-model-small-en-us /app/vosk-model-small-en-us
COPY --from=builder /build/onnx-models /app/onnx-models

# Copy the source code
COPY --from=builder /build/src /app/src

RUN python3 -c "import zmq; print('ZMQ Installed:', zmq.__version__)"

RUN mkdir -p /root/.config/pulse && \
    [ ! -d /root/.config/pulse/cookie ] || rm -rf /root/.config/pulse/cookie

# Copy entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

# Start the app
#CMD ["python3", "/app/src/vosk_service.py"]

