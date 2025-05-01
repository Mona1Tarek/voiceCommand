#!/bin/bash
set -e

# Ensure we're using the Python virtual environment
export PATH="/app/venv/bin:$PATH"
export PYTHONPATH="/app"

# Check if the ONNX model exists and has a non-zero size
# MODEL_PATH="/app/onnx-models/all-MiniLM-L6-v2-onnx/model.onnx"
# if [ ! -s "$MODEL_PATH" ]; then
#     echo "ONNX model not found or has zero size. Creating dummy model..."
#     python3 create_dummy_model.py
# else
#     echo "ONNX model found."
# fi

# Start the voice service in standalone mode with direct audio recognition
echo "Starting voice command service..."
python3 src/vosk_service.py

# If any specific command passed, execute it instead
if [ $# -gt 0 ]; then
    exec "$@"
fi 