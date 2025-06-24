# Build stage
FROM ubuntu:22.04 AS builder

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install build dependencies including libzmq3-dev for pyzmq
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
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
RUN pip3 install pyzmq pyaudio scipy

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
    unzip /build/vosk-model-small-en-us/vosk-model-small-en-us-0.15.zip -d /build/vosk-model-small-en-us-0.15 && \
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

RUN pip3 install pyzmq

# Set working directory
WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages

# Copy the required models
COPY --from=builder /build/vosk-model-small-en-us-0.15 /app/vosk-model-small-en-us
COPY --from=builder /build/onnx-models /app/onnx-models

# Copy the source code
COPY --from=builder /build/src /app/src

# Copy entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Start the app
CMD ["python3", "/app/src/vosk_service.py"]
