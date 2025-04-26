import pyaudio
import json
from vosk import Model, KaldiRecognizer
import chromadb
import os
from embedding_handler import ONNXEmbeddingHandler

class VoskService:
    def __init__(self, model_path="vosk-model-small-en-us-0.15"):
        """
        Initialize the Vosk speech recognition service with ChromaDB integration.
        
        Args:
            model_path (str): Path to the Vosk model directory
        """
        # Initialize Vosk
        self.model = Model(model_path)
        
        # Get sample rate from environment variable if set by check_audio.py
        if 'AUDIO_SAMPLE_RATE' in os.environ:
            self.samplerate = int(os.environ['AUDIO_SAMPLE_RATE'])
            print(f"Using audio sample rate from environment: {self.samplerate} Hz")
        else:
            self.samplerate = 16000  # Default rate for speech recognition
            print(f"Using default audio sample rate: {self.samplerate} Hz")
            
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.recognizer = None

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
        """Start the audio stream and recognizer"""
        # Find a suitable input device
        input_device_index = None
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if device_info["maxInputChannels"] > 0:
                input_device_index = i
                print(f"Using input device: {device_info['name']}")
                break
        
        if input_device_index is None:
            print("No suitable input device found")
        
        # Define fallback sample rates
        sample_rates = [
            self.samplerate,  # Try the configured rate first
            44100,  # Standard rate for most audio devices
            48000,  # Another common rate
            22050,  # Lower standard rate
            8000    # Lowest rate for last resort
        ]
        
        # Remove duplicates while preserving order
        sample_rates = list(dict.fromkeys(sample_rates))
        
        stream_opened = False
        for rate in sample_rates:
            try:
                print(f"Trying to open audio stream with sample rate: {rate} Hz")
                self.stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=rate,
                    input=True,
                    input_device_index=input_device_index,
                    frames_per_buffer=4000
                )
                self.stream.start_stream()
                
                # Update samplerate if we're using a different one
                if rate != self.samplerate:
                    print(f"Using alternative sample rate: {rate} Hz")
                    self.samplerate = rate
                    # Update the environment variable
                    os.environ['AUDIO_SAMPLE_RATE'] = str(rate)
                    
                self.recognizer = KaldiRecognizer(self.model, self.samplerate)
                stream_opened = True
                print(f"Successfully opened audio stream at {rate} Hz")
                break
            except Exception as e:
                print(f"Failed to open stream at {rate} Hz: {str(e)}")
        
        if not stream_opened:
            print("Could not open audio stream with any sample rate")
            # If we have an error, just proceed without the stream for WAV file testing
            self.recognizer = KaldiRecognizer(self.model, self.samplerate)

    def stop(self):
        """Stop the audio stream and cleanup"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

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
        Continuously listen and process audio from the microphone
        
        Yields:
            dict: Recognition results with command matching
        """
        self.start()
        try:
            while True:
                if not self.stream:
                    print("No audio stream available")
                    break
                    
                data = self.stream.read(4000, exception_on_overflow=False)
                result = self.predict(data)
                
                if result:
                    if "text" in result and result["text"]:
                        # Find matching command
                        matched_text, action = self.find_matching_command(result["text"])
                        if matched_text:
                            result["matched_command"] = matched_text
                            result["action"] = action
                    yield result
        finally:
            self.stop()

if __name__ == "__main__":
    # Example usage
    service = VoskService()
    
    # Add some example commands
    service.add_command("1", "lock the doors", "lock_doors")
    service.add_command("2", "unlock the doors", "unlock_doors")
    service.add_command("3", "stop the car", "stop_the_car")
    service.add_command("4", "turn on the headlights", "turn_on_the_headlights")
    service.add_command("5", "open the window", "window_open")
    service.add_command("6", "turn on the ac", "turn_on_the_ac")
    
    print("Start speaking...")
    try:
        for result in service.listen():
            if "text" in result and result["text"]:
                print(f"\nRecognized: {result['text']}")
                if "matched_command" in result:
                    print(f"Matched Command: {result['matched_command']}")
                    print(f"Action: {result['action']}")
            elif "partial" in result and result["partial"]:
                print(f"Listening: {result['partial']}", end="\r")
    except KeyboardInterrupt:
        print("\nStopping recognition...")
    finally:
        service.stop() 