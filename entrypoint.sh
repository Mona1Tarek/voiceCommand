#!/bin/bash
set -e

# Ensure we're using the Python virtual environment
#export PATH="/app/venv/bin:$PATH"
export PYTHONPATH="/app"

# Audio device setup and debugging information
echo "=== Audio Device Information ==="

# List ALSA devices
echo "ALSA devices:"
aplay -l

# List PulseAudio devices if available
if command -v pactl &> /dev/null; then
    echo "PulseAudio devices:"
    pactl list sources | grep -e "Name:" -e "device.description"
fi

# Create a default PulseAudio client config if it doesn't exist
if [ ! -f "/etc/pulse/client.conf" ]; then
    cat > /etc/pulse/client.conf << EOF
default-server = unix:/run/pulse/native
autospawn = no
daemon-binary = /bin/true
enable-shm = false
EOF
    echo "Created PulseAudio client config"
fi

echo "=== Audio Setup Complete ==="

# Start the voice service in standalone mode with direct audio recognition
echo "Starting voice command service..."
python3 src/vosk_service.py

# If any specific command passed, execute it instead
if [ $# -gt 0 ]; then
    exec "$@"
fi