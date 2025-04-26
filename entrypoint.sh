#!/bin/bash
set -e

echo "Checking audio device configuration..."
python3 check_audio.py || true

echo -e "\n\n================================================\n"
echo "Testing ONNX Embedding Handler..."
python3 test_embedding.py || true

echo -e "\n\n================================================\n"
echo "Running Vosk Service Test..."
python3 test_vosk_service.py


# If any specific command passed, execute it instead
if [ $# -gt 0 ]; then
    exec "$@"
fi 