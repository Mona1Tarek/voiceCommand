import time
import wave
import json
from vosk import Model, KaldiRecognizer
from src.vosk_service import VoskService

def test_basic_recognition():
    """Test basic speech recognition functionality"""
    print("\n=== Testing Basic Recognition ===")
    service = VoskService(model_path="../vosk-model-small-en-us-0.15")
    
    try:
        service.start()
        print("Start speaking (say 'hello' or any other word)...")
        
        # Listen for 5 seconds
        start_time = time.time()
        while time.time() - start_time < 5:
            data = service.stream.read(4000)
            result = service.predict(data)
            
            if result and "text" in result and result["text"]:
                print(f"Recognized: {result['text']}")
                break
                
            if result and "partial" in result and result["partial"]:
                print(f"Partial: {result['partial']}", end="\r")
                
    finally:
        service.stop()

def test_continuous_listening():
    """Test continuous listening with the generator method"""
    print("\n=== Testing Continuous Listening ===")
    service = VoskService(model_path="../vosk-model-small-en-us-0.15")
    
    print("Start speaking (press Ctrl+C to stop)...")
    try:
        for result in service.listen():
            if "text" in result and result["text"]:
                print(f"Recognized: {result['text']}")
            elif "partial" in result and result["partial"]:
                print(f"Partial: {result['partial']}", end="\r")
    except KeyboardInterrupt:
        print("\nStopping recognition...")
    finally:
        service.stop()

def test_custom_model_path():
    """Test using a custom model path"""
    print("\n=== Testing Custom Model Path ===")
    custom_model_path = "../vosk-model-small-en-us-0.15"
    service = VoskService(model_path=custom_model_path)
    
    try:
        service.start()
        print("Start speaking (say something)...")
        
        # Listen for 3 seconds
        start_time = time.time()
        while time.time() - start_time < 3:
            data = service.stream.read(4000)
            result = service.predict(data)
            
            if result and "text" in result and result["text"]:
                print(f"Recognized: {result['text']}")
                break
                
    finally:
        service.stop()

def test_wav_file_with_commands():
    """Test speech recognition on a WAV file with command matching"""
    print("\n=== Testing WAV File Recognition with Command Matching ===")
    
    try:
        # Initialize service
        service = VoskService(model_path="../vosk-model-small-en-us-0.15")
        
        # Add test commands
        service.add_command("1", "lock the doors", "lock_doors")
        service.add_command("2", "unlock the doors", "unlock_doors")
        service.add_command("3", "stop the car", "stop_the_car")
        service.add_command("4", "turn on the headlights", "turn_on_the_headlights")
        service.add_command("5", "open the window", "window_open")
        service.add_command("6", "turn on the ac", "turn_on_the_ac")
    
        wf = None
        try:
            # Open the WAV file
            wf = wave.open("test.wav", "rb")
            
            # Check if the audio format is compatible
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                print("Audio file must be WAV format mono PCM.")
                return
                
            # Initialize the recognizer with the WAV file sample rate
            sample_rate = wf.getframerate()
            print(f"WAV file sample rate: {sample_rate}")
            service.recognizer = KaldiRecognizer(service.model, sample_rate)
            
            print("Processing WAV file...")
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                    
                if service.recognizer.AcceptWaveform(data):
                    result = service.recognizer.Result()
                    if result:
                        result_dict = json.loads(result)
                        if result_dict.get("text"):
                            print(f"\nRecognized: {result_dict['text']}")
                            # Find matching command
                            matched_text, action = service.find_matching_command(result_dict["text"])
                            if matched_text:
                                print(f"Matched Command: {matched_text}")
                                print(f"Action to perform: {action}")
                else:
                    result = service.recognizer.PartialResult()
                    if result:
                        result_dict = json.loads(result)
                        if result_dict.get("partial"):
                            print(f"Partial: {result_dict['partial']}", end="\r")
                            
            # Get final result
            final_result = service.recognizer.FinalResult()
            if final_result:
                result_dict = json.loads(final_result)
                if result_dict.get("text"):
                    print(f"\nFinal result: {result_dict['text']}")
                    # Find matching command for final result
                    matched_text, action = service.find_matching_command(result_dict["text"])
                    if matched_text:
                        print(f"Matched Command: {matched_text}")
                        print(f"Action to perform: {action}")
                    
        except FileNotFoundError:
            print("Error: test.wav file not found")
        except Exception as e:
            print(f"Error processing WAV file: {str(e)}")
        finally:
            if wf:
                wf.close()
    except Exception as outer_e:
        print(f"Error in test setup: {str(outer_e)}")

if __name__ == "__main__":
    print("Vosk Service Test Suite")
    print("=======================")
    
    # Focus only on WAV file testing
    test_wav_file_with_commands()
    
    print("\nAll tests completed!") 