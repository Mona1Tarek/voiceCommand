import pyaudio
import json
from vosk import Model, KaldiRecognizer
import chromadb
import os
import numpy as np
from scipy import signal
from embedding_handler import ONNXEmbeddingHandler
import sys
import zmq 

class VoskService:
    def __init__(self, model_path="vosk-model-small-en-us/vosk-model-small-en-us-0.15", input_device_index=None, zmq_port=5555):
        """
        Initialize the Vosk speech recognition service with ChromaDB integration.
        
        Args:
            model_path (str): Path to the Vosk model directory
            input_device_index (int, optional): Index of input device to use. If None, will attempt to auto-detect.
            zmq_port (int, optional): Port number for ZMQ publisher. Defaults to 5555.
        """

        # Initialize ZMQ publisher
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{zmq_port}")
        print(f"ZMQ publisher started on port {zmq_port}")
        
        # Initialize Vosk - use fixed 16000 Hz sample rate for better recognition
        self.model = Model(model_path)
        self.samplerate = 16000  # Fixed 16000 Hz - optimal for Vosk models
        self.frames_per_buffer = 4000
        print(f"Using sample rate for recognition: {self.samplerate} Hz")
        
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.recognizer = None
        self.input_device_index = input_device_index
        
        # Initialize ONNX embeddings handler
        self.embedding_handler = ONNXEmbeddingHandler()
        
        # Initialize ChromaDB (use PersistentClient instead of HttpClient)
        # For local standalone usage
        self.chroma_client = chromadb.Client()
        
        # Create a collection with embedding function from handler
        try:
            # Try to reset collection if it exists
            try:
                self.chroma_client.delete_collection("voice_commands")
                print("Deleted existing voice_commands collection")
            except:
                pass
            
            # Create new collection
            self.commands_collection = self.chroma_client.create_collection(
                name="voice_commands",
                embedding_function=self.embedding_handler.get_embedding_function()
            )
            print("Created new voice_commands collection")
        except Exception as e:
            print(f"Error creating ChromaDB collection: {str(e)}")
            raise

    def add_command(self, command_id, command_text, action):
        """
        Add a voice command to the ChromaDB collection.
        
        Args:
            command_id (str): Unique identifier for the command
            command_text (str): The text of the voice command
            action (str): The action to perform when this command is recognized
        """
        self.commands_collection.add(
            documents=[command_text],
            ids=[command_id],
            metadatas=[{"action": action}]
        )

    def start(self):
        """Start the audio stream and recognizer - using simplified approach"""
        print("Initializing audio stream...")
        
        try:
            # List all available audio devices
            print("\n=== Available Audio Input Devices ===")
            default_device_index = self.p.get_default_input_device_info()['index'] if self.input_device_index is None else self.input_device_index
            print(f"Default input device index: {default_device_index}")
            
            for i in range(self.p.get_device_count()):
                device_info = self.p.get_device_info_by_index(i)
                if device_info["maxInputChannels"] > 0:
                    print(f"Device {i}: {device_info['name']}")
                    if "pulse" in device_info['name'].lower() and self.input_device_index is None:
                        default_device_index = i
                        print(f"  Auto-selected PulseAudio device")
            
            # Use the detected device index or the one provided
            input_device_index = default_device_index
            print(f"Using input device index: {input_device_index}")
            
            # Open stream with fixed 16000 Hz rate - optimal for Vosk models
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.samplerate,
                input=True,
                frames_per_buffer=self.frames_per_buffer,
                input_device_index=input_device_index
            )
            self.stream.start_stream()
            print(f"Audio stream started at {self.samplerate} Hz")
            
            # Initialize recognizer with standard rate for Vosk
            self.recognizer = KaldiRecognizer(self.model, self.samplerate)
            print("Recognizer initialized")
            
        except Exception as e:
            print(f"Error starting audio stream: {str(e)}")
            # If we have an error, just proceed without the stream for WAV file testing
            self.recognizer = KaldiRecognizer(self.model, self.samplerate)
            print("Using recognizer without stream due to error")

    def stop(self):
        """Stop the audio stream and cleanup"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        self.socket.close()
        self.context.term()
        print("Audio stream stopped")

    def predict(self, data):
        """
        Process audio data and return recognition results
        
        Args:
            data (bytes): Audio data to process
            
        Returns:
            dict: Recognition results including text and confidence
        """
        if self.recognizer.AcceptWaveform(data):
            result = json.loads(self.recognizer.Result())
            return result
        return json.loads(self.recognizer.PartialResult())

    def find_matching_command(self, text):
        """
        Find the best matching voice command using ChromaDB.
        
        Args:
            text (str): Recognized speech text
            
        Returns:
            tuple: (matched_text, action) or (None, None) if no match found
        """
        if not text.strip():
            return None, None

        results = self.commands_collection.query(
            query_texts=[text],
            n_results=1
        )

        if results['documents'] and results['documents'][0]:
            matched_text = results['documents'][0][0]
            matched_action = results['metadatas'][0][0]['action']
            return matched_text, matched_action
        return None, None

    def listen(self):
        """
        Continuously listen and process audio from the microphone.
        Simplified to match mainAudioLive.py functionality.
        
        Yields:
            dict: Recognition results with command matching
        """
        self.start()
        print("Start speaking...")
        
        try:
            while True:
                if not self.stream:
                    print("No audio stream available")
                    break
                
                # Simple, direct reading from the stream - like in mainAudioLive.py
                data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
                
                # Process the audio data
                if self.recognizer.AcceptWaveform(data):
                    result_json = self.recognizer.Result()
                    result = json.loads(result_json)
                    print(f"Result JSON: {result}")


                    if "text" in result and result["text"].strip():
                        print(f"Recognized: {result['text']}")
                        
                        # Find matching command
                        matched_text, action = self.find_matching_command(result["text"])
                        if matched_text:
                            result["matched_command"] = matched_text
                            result["action"] = action
                            print(f"Matched command: {matched_text}")
                            print(f"Action: {action}")

                            # Publish the action via ZMQ
                            self.socket.send_string(f"action {action}")
                            print(f"Published action: {action}")
                        
                        yield result
                
                # Handle partial results
                partial_json = self.recognizer.PartialResult()
                partial = json.loads(partial_json)
                
                if "partial" in partial and partial["partial"].strip():
                    print(f"Listening: {partial['partial']}", end="\r")
                    yield partial
                
        except Exception as e:
            print(f"Error in listen loop: {str(e)}")
        finally:
            self.stop()
            
    def run_standalone(self):
        """
        Run the service in standalone mode, similar to mainAudioLive.py
        """
        # Add some example commands
        self.add_command("1", "lock the doors", "lock_doors")
        self.add_command("2", "unlock the doors", "unlock_doors")
        self.add_command("3", "stop the car", "stop_the_car")
        self.add_command("4", "turn on the headlights", "turn_on_the_headlights")
        self.add_command("5", "open the window", "window_open")
        self.add_command("6", "turn on the ac", "turn_on_the_ac")
        
        try:
            for result in self.listen():
                if "text" in result and result["text"].strip():
                    print(f"\nRecognized: {result['text']}")
                    
                    if "matched_command" in result:
                        print(f"Matched Command: {result['matched_command']}")
                        print(f"Action: {result['action']}")
        except KeyboardInterrupt:
            print("\nStopping recognition...")
        finally:
            self.stop()

if __name__ == "__main__":
    # Check if an input device index is provided as a command line argument
    input_device_index = None
    zmq_port = 5555  # Default ZMQ port

    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        input_device_index = int(sys.argv[1])
        print(f"Using command line provided input device index: {input_device_index}")
    
    if len(sys.argv) > 2:
        if sys.argv[2].isdigit():
            zmq_port = int(sys.argv[2])
            print(f"Using command line provided ZMQ port: {zmq_port}")
    
    # Example usage - run standalone like mainAudioLive.py
    service = VoskService(input_device_index=input_device_index, zmq_port=zmq_port)
    service.run_standalone()