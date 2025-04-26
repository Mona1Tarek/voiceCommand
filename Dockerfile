FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Vosk model and source code
COPY vosk-model-small-en-us-0.15 /app/vosk-model-small-en-us-0.15
COPY vosk_service.py .

# Run the service
CMD ["python", "vosk_service.py"] 