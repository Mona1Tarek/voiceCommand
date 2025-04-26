# Vosk Speech Recognition Service with ONNX Embeddings

This is a Dockerized service for speech recognition using Vosk with semantic matching powered by ONNX embeddings.

## Features

- Speech recognition with Vosk
- Semantic command matching using ONNX embeddings
- Docker containerization for easy deployment
- Works with both microphone input and WAV files
- Supports offline use

## Prerequisites

- Docker installed on your system
- Docker Compose (optional but recommended)
- Vosk model (downloaded automatically in the Docker build)

## Quick Start

The easiest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/yourusername/voiceCommand.git
cd voiceCommand

# Build and run with Docker Compose
docker-compose up --build
```

## Alternative Setup (if experiencing network issues)

If you're experiencing network issues during the Docker build:

```bash
# Use the alternative Docker Compose file
docker-compose -f docker-compose.alt.yml up --build
```

## Manual Setup

If you prefer to set up the components manually:

1. Download the Vosk model:
```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the tests:
```bash
python test_embedding.py
python test_vosk_service.py
```

## API

The `VoskService` class provides the following methods:

- `start()`: Initialize the audio stream and recognizer
- `stop()`: Clean up resources
- `predict(data)`: Process audio data and return recognition results
- `listen()`: Continuously listen and process audio from the microphone
- `add_command(command_id, command_text, action)`: Add a voice command
- `find_matching_command(text)`: Find the best matching command

## Embedding Handler

The `ONNXEmbeddingHandler` class provides efficient embedding generation:

- `encode(texts)`: Generate embeddings for input texts
- `get_embedding_function()`: Get a ChromaDB-compatible embedding function

## Example

```python
from vosk_service import VoskService

# Initialize service
service = VoskService()

# Add commands
service.add_command("1", "lock the doors", "lock_doors")
service.add_command("2", "unlock the doors", "unlock_doors")
service.add_command("3", "stop the car", "stop_the_car")

# Start listening
for result in service.listen():
    if "text" in result:
        print(f"Recognized: {result['text']}")
        if "matched_command" in result:
            print(f"Matched: {result['matched_command']}")
            print(f"Action: {result['action']}")
```

## Troubleshooting

### Audio Issues

If you encounter audio device issues:

- Run `python check_audio.py` to diagnose audio device configuration
- Make sure you mount `/dev/snd` when running in Docker
- Check if your system has a working microphone

### Network Issues

If you have network connectivity problems during the build:

- Use the alternative Dockerfile (`Dockerfile.alt`)
- The system will create a dummy ONNX model if downloads fail
- All functionality will still work, but with less accurate embeddings

### ONNX Model Issues

If the ONNX model fails to load:

- The system will automatically fall back to a simpler implementation
- All functionality will still work, but with deterministic random embeddings

## License

This project is licensed under the MIT License - see the LICENSE file for details. 