import sys
import os
import platform

def check_audio_devices():
    """
    Check available audio devices and their configurations
    """
    print("System Information:")
    print(f"  Python version: {sys.version}")
    print(f"  Platform: {platform.platform()}")
    print(f"  System: {platform.system()} {platform.release()}")
    
    # Check for PortAudio library
    print("\nChecking libraries:")
    for lib_dir in ['/usr/lib', '/usr/local/lib']:
        if os.path.exists(lib_dir):
            print(f"Contents of {lib_dir} related to PortAudio:")
            os.system(f"find {lib_dir} -name '*portaudio*' | sort")
    
    # Check for PyAudio module
    print("\nPython module information:")
    for path in sys.path:
        if os.path.exists(path):
            os.system(f"find {path} -name 'pyaudio*' | sort")
    
    try:
        print("\nImporting PyAudio...")
        import pyaudio
        print("PyAudio imported successfully!")
        
        # Check PyAudio binary details
        import inspect
        print(f"PyAudio module location: {inspect.getfile(pyaudio)}")
        
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        
        print(f"PyAudio version: {pyaudio.get_portaudio_version_text()}")
        print(f"Total devices found: {device_count}")
        
        print("\nAudio Device Information:")
        print("=" * 50)
        
        try:
            default_input = p.get_default_input_device_info()
            print(f"Default input device: {default_input}")
        except Exception as e:
            print(f"Error getting default input device: {str(e)}")
        
        try:
            default_output = p.get_default_output_device_info()
            print(f"Default output device: {default_output}")
        except Exception as e:
            print(f"Error getting default output device: {str(e)}")
        
        for i in range(device_count):
            try:
                device_info = p.get_device_info_by_index(i)
                print(f"\nDevice {i}:")
                print(f"  Name: {device_info['name']}")
                print(f"  Max Input Channels: {device_info['maxInputChannels']}")
                print(f"  Max Output Channels: {device_info['maxOutputChannels']}")
                print(f"  Default Sample Rate: {device_info['defaultSampleRate']}")
            except Exception as e:
                print(f"\nDevice {i}: Error getting info - {str(e)}")
        
        # Test opening a stream
        print("\nTesting audio stream open...")
        
        # Try multiple sample rates if needed
        sample_rates = [
            # 16000,  # First try the desired rate for speech recognition
            44100,  # Standard rate for most audio devices
            # 48000,  # Another common rate
            # 22050,  # Lower standard rate
            # 8000    # Lowest rate for last resort
        ]
        
        # Get default device's preferred sample rate
        try:
            default_device = p.get_default_input_device_info()
            default_rate = int(default_device['defaultSampleRate'])
            print(f"  Default device sample rate: {default_rate}")
            # Prioritize the device's default rate by inserting it at the beginning
            if default_rate not in sample_rates:
                sample_rates.insert(0, default_rate)
        except Exception as e:
            print(f"  Could not get default device sample rate: {str(e)}")
        
        # Try opening stream with different sample rates
        success = False
        for rate in sample_rates:
            try:
                print(f"  Trying sample rate: {rate} Hz")
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=rate,
                    input=True,
                    frames_per_buffer=1024
                )
                stream.stop_stream()
                stream.close()
                print(f"  Success: Audio input stream opened at {rate} Hz")
                success = True
                
                # Save successful rate to an environment variable for other scripts to use
                os.environ['AUDIO_SAMPLE_RATE'] = str(rate)
                print(f"  Set AUDIO_SAMPLE_RATE={rate}")
                break
            except Exception as e:
                print(f"  Failed at {rate} Hz: {str(e)}")
        
        if not success:
            print("  Error: Could not open audio stream with any sample rate")
            
        p.terminate()
        print("\nAudio check complete.")
        
    except ImportError as e:
        print(f"Error importing PyAudio: {str(e)}")
        print("\nDetailed import information:")
        
        try:
            # Check Python import path
            print("\nPython module paths:")
            for p in sys.path:
                print(f"  {p}")
            
            # Try to find PyAudio module in filesystem
            print("\nSearching for PyAudio files:")
            os.system("find /usr -name '*pyaudio*' | sort")
            
            # Check if PortAudio is installed
            print("\nChecking for PortAudio:")
            os.system("ldconfig -p | grep portaudio")
            
            # Check shared library dependencies
            try:
                import ctypes
                print("\nAttempting to load PortAudio directly via ctypes:")
                portaudio = ctypes.CDLL('libportaudio.so.2')
                print("  Success: libportaudio.so.2 loaded successfully!")
            except Exception as e:
                print(f"  Error loading libportaudio.so.2: {str(e)}")
            
        except Exception as detailed_e:
            print(f"Error during detailed diagnosis: {str(detailed_e)}")
        
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error initializing PyAudio: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Checking audio devices...")
    check_audio_devices() 