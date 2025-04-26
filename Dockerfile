FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive 
ENV PYTHONUNBUFFERED=1

# Install Python and audio dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev \
    libasound2-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
&& apt-get install libportaudio2 libportaudiocpp0 portaudio19-dev libsndfile1-dev -y \
&& pip3 install pyaudio

# Set working directory
WORKDIR /app

# Install PyAudio explicitly
RUN pip3 install pyaudio
RUN python3 -m pip install --upgrade pip

# Copy requirements file (excluding PyAudio)
COPY requirements.txt .

# Install Python dependencies
RUN sed -i '/pyaudio/d' requirements.txt && \
    pip3 install --no-cache-dir -r requirements.txt

# Create directory for ONNX models
RUN mkdir -p /app/onnx-models/all-MiniLM-L6-v2-onnx

# Copy the Vosk model and source code
COPY vosk-model-small-en-us-0.15 /app/vosk-model-small-en-us-0.15
COPY vosk_service.py .
COPY test_vosk_service.py .
COPY embedding_handler.py .
COPY test_embedding.py .
COPY check_audio.py .
COPY test.wav .

# Attempt to download the ONNX model, but if it fails, create a dummy one
RUN wget --tries=2 --timeout=10 -O /app/onnx-models/all-MiniLM-L6-v2-onnx/model.onnx https://huggingface.co/onnx-models/all-MiniLM-L6-v2-onnx/resolve/main/model.onnx || \
    wget --tries=2 --timeout=10 -O /app/onnx-models/all-MiniLM-L6-v2-onnx/model.onnx https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/model.onnx || \
    (echo "Warning: Failed to download ONNX model. Will use fallback at runtime." && \
     python3 create_dummy_model.py)

# Setup entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Default command: run test_vosk_service.py
CMD ["/app/entrypoint.sh"] 