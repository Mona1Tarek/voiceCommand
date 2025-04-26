# Vosk Speech Recognition Service

This is a Dockerized service for speech recognition using Vosk.

## Prerequisites

- Docker installed on your system
- Vosk model downloaded and placed in the project directory

## Setup

1. Download the Vosk model:
```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

2. Build the Docker image:
```bash
docker build -t vosk-service .
```

3. Run the container:
```bash
docker run --device /dev/snd:/dev/snd vosk-service
```

## Usage

The service will start listening to your microphone input and print recognized text to the console.

## API

The `VoskService` class provides the following methods:

- `start()`: Initialize the audio stream and recognizer
- `stop()`: Clean up resources
- `predict(data)`: Process audio data and return recognition results
- `listen()`: Continuously listen and process audio from the microphone

## Example

```python
from vosk_service import VoskService

service = VoskService()
service.start()

try:
    for result in service.listen():
        if "text" in result:
            print(f"Recognized: {result['text']}")
        elif "partial" in result:
            print(f"Partial: {result['partial']}", end="\r")
finally:
    service.stop()
``` 