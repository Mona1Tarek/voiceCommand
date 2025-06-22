# Build stage
FROM ubuntu:22.04 AS builder

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive 
ENV PYTHONUNBUFFERED=1

# Install build dependencies including libzmq3-dev for pyzmq
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev python3-venv \
    libzmq3-dev \
    libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev \
    libasound2-dev \
    alsa-utils \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Create and activate Python virtual environment
RUN python3 -m venv /build/venv
ENV PATH="/build/venv/bin:$PATH"
RUN pip3 install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install pyaudio scipy

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

# Final production stage
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Install only minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-venv \
    libasound-dev libportaudio2 libportaudiocpp0 \
    pulseaudio-utils pulseaudio \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Create pulse config directory
RUN mkdir -p /etc/pulse

# Set working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /build/venv /app/venv

# Copy the required models
COPY --from=builder /build/vosk-model-small-en-us-0.15 /app/vosk-model-small-en-us
COPY --from=builder /build/onnx-models /app/onnx-models

# Copy the source code
COPY --from=builder /build/src /app/src

# Copy entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Default command
# CMD ["/app/entrypoint.sh"]
