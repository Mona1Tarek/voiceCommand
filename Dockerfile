FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    libzmq3-dev \
    libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev \
    pulseaudio-utils pulseaudio \
    alsa-utils wget unzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install pyzmq pyaudio scipy

# Copy source code
COPY src /app/src

# Download ONNX model
RUN mkdir -p /app/onnx-models/all-MiniLM-L6-v2-onnx && \
    wget --tries=2 --timeout=10 -O /app/onnx-models/all-MiniLM-L6-v2-onnx/model.onnx \
    https://huggingface.co/onnx-models/all-MiniLM-L6-v2-onnx/resolve/main/model.onnx || \
    wget --tries=2 --timeout=10 -O /app/onnx-models/all-MiniLM-L6-v2-onnx/model.onnx \
    https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/model.onnx || \
    (echo "Warning: Failed to download ONNX model.")

# Download and extract VOSK model
RUN mkdir -p /app/vosk-model-small-en-us && \
    wget --tries=2 --timeout=10 -O /app/vosk.zip \
    https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && \
    unzip /app/vosk.zip -d /app/vosk-model-small-en-us && \
    rm /app/vosk.zip

# Add entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Start the service
CMD ["python3", "/app/src/vosk_service.py"]
