# Build stage
FROM ubuntu:22.04 AS builder

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive 
ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev python3-venv \
    libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev \
    libasound2-dev \
    alsa-utils \
    wget \
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

# Copy the source code for testing
COPY embedding_handler.py .
COPY vosk_service.py .
COPY test_embedding.py test_vosk_service.py check_audio.py ./
COPY test.wav ./

# Create directory for ONNX models
RUN mkdir -p /build/onnx-models/all-MiniLM-L6-v2-onnx

# Attempt to download the ONNX model, but if it fails, create a dummy one
RUN wget --tries=2 --timeout=10 -O /build/onnx-models/all-MiniLM-L6-v2-onnx/model.onnx \
    https://huggingface.co/onnx-models/all-MiniLM-L6-v2-onnx/resolve/main/model.onnx || \
    wget --tries=2 --timeout=10 -O /build/onnx-models/all-MiniLM-L6-v2-onnx/model.onnx \
    https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/model.onnx || \
    (echo "Warning: Failed to download ONNX model. Will create dummy model." && \
     python3 create_dummy_model.py)

# Copy the Vosk model
COPY vosk-model-small-en-us-0.15 /build/vosk-model-small-en-us-0.15


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
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /build/venv /app/venv

# Copy only the necessary files for production
COPY --from=builder /build/vosk-model-small-en-us-0.15 /app/vosk-model-small-en-us-0.15
COPY --from=builder /build/onnx-models /app/onnx-models
COPY vosk_service.py embedding_handler.py test_vosk_service.py /app/

# Create a simple entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Default command: run the entrypoint script
# CMD ["/app/entrypoint.sh"] 