import pyaudio
import numpy as np
import time

def test_microphone():
    """Simple script to test microphone input"""
    print("=== Microphone Input Test ===")
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Print available input devices
    print("\nAvailable Input Devices:")
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info["maxInputChannels"] > 0:
            print(f"  Device {i}: {device_info['name']}")
    
    # Parameters
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024  # Number of frames per buffer
    
    # Open microphone stream
    print("\nOpening microphone stream...")
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=4

        )
        
        print("Microphone stream opened successfully!")
        print("Listening... (Press Ctrl+C to stop)")
        
        # Listen and print audio levels
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            # Convert data to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Check if audio data is valid
            if len(audio_data) > 0:
                # Calculate volume level (simple RMS)
                square_data = np.square(audio_data).astype(np.float64)
                mean_square = np.mean(square_data)
                
                # Prevent NaN by checking for valid value
                if mean_square > 0:
                    volume = np.sqrt(mean_square)
                else:
                    volume = 0.0
                
                # Print a visual representation of volume (with safe integer conversion)
                bars = max(0, min(50, int(volume / 100)))
                print(f"Volume: {volume:.2f} " + "#" * bars, end="\r")
            else:
                print("No audio data received", end="\r")
                
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nStopping microphone test...")
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        # Clean up
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()
        print("Microphone test completed.")

if __name__ == "__main__":
    test_microphone()