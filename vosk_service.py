import pyaudio
import json
from vosk import Model, KaldiRecognizer
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import os

class VoskService:
    def __init__(self, model_path="vosk-model-small-en-us-0.15"):
        """
        Initialize the Vosk speech recognition service with ChromaDB integration.
        
        Args:
            model_path (str): Path to the Vosk model directory
        """
        # Initialize Vosk
        self.model = Model(model_path)
        self.samplerate = 16000
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.recognizer = None

        # Initialize ChromaDB
        self.embedding_function = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.chroma_client = chromadb.HttpClient(
            host="chromadb",
            port=8000
        )
        self.commands_collection = self.chroma_client.create_collection(
            name="voice_commands",
            embedding_function=self.embedding_function
        )

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
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.samplerate,
            input=True,
            frames_per_buffer=4000
        )
        self.stream.start_stream()
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
                data = self.stream.read(4000)
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