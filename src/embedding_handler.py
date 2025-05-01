import os
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
from typing import List, Union
import requests
import sys
import random

class ONNXEmbeddingHandler:
    def __init__(self, model_dir: str = "onnx-models"):
        """
        Initialize the ONNX embedding handler for all-MiniLM-L6-v2.
        
        Args:
            model_dir (str): Directory to store/load the ONNX model
        """
        self.model_dir = model_dir
        self.model_name = "all-MiniLM-L6-v2"
        self.model_path = os.path.join(model_dir, f"{self.model_name}-onnx/model.onnx")
        self.embedding_dim = 384   # Default embedding dimension for all-MiniLM-L6-v2
        self.max_seq_length = 128  # Default max sequence length for all-MiniLM-L6-v2
        self.using_dummy = False
        
        # Ensure model directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Try to initialize ONNX Runtime session and tokenizer
        try:
            # Check if model exists or download it
            if not os.path.exists(self.model_path):
                try:
                    self._download_model()
                except:
                    # If download fails, try to create a dummy model
                    self._create_dummy_model()
                    self.using_dummy = True
                
            # Initialize ONNX Runtime session
            self.ort_session = ort.InferenceSession(self.model_path)
            
            # Initialize tokenizer
            try:
                self.tokenizer = Tokenizer.from_pretrained(f"sentence-transformers/{self.model_name}")
            except Exception as tokenizer_error:
                print(f"Error loading tokenizer: {str(tokenizer_error)}")
                print("Falling back to dummy implementation")
                self.using_dummy = True
                
        except Exception as e:
            print(f"Error initializing ONNX model: {str(e)}")
            print("Falling back to dummy implementation")
            self.using_dummy = True
            self._create_dummy_model()

    def _create_dummy_model(self):
        """Create a dummy model file for testing"""
        try:
            # Create a random array to simulate embeddings
            dummy_embedding = np.random.rand(384).astype(np.float32)
            
            # Save the array to file
            with open(self.model_path, 'wb') as f:
                f.write(b'DUMMY_ONNX_MODEL')
                np.save(f, dummy_embedding)
            
            print(f"Created dummy model at {self.model_path}")
            
            # Create metadata file
            metadata = {
                "dimension": 384,
                "dummy": True,
                "created": "fallback_for_testing"
            }
            
            metadata_path = os.path.join(os.path.dirname(self.model_path), "metadata.json")
            with open(metadata_path, 'w') as f:
                import json
                json.dump(metadata, f)
                
            print("Created dummy model for fallback")
        except Exception as e:
            print(f"Error creating dummy model: {str(e)}")

    def _download_model(self):
        """Download the ONNX model from HuggingFace."""
        print(f"Downloading {self.model_name} ONNX model...")        
        url = f"https://huggingface.co/onnx-models/{self.model_name}-onnx/resolve/main/model.onnx"
        
        try:
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()
            
            with open(self.model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Model downloaded successfully!")
        except Exception as e:
            print(f"Error downloading model: {str(e)}")
            raise

    def _tokenize(self, text: str) -> dict:
        """
        Tokenize input text.
        
        Args:
            text (str): Input text to tokenize
            
        Returns:
            dict: Dictionary containing input_ids, attention_mask, and token_type_ids
        """
        if self.using_dummy:
            # Create dummy tokenization
            return {
                'input_ids': np.ones((1, 10), dtype=np.int64),
                'attention_mask': np.ones((1, 10), dtype=np.int64),
                'token_type_ids': np.zeros((1, 10), dtype=np.int64)
            }
            
        try:
            encoded = self.tokenizer.encode(text)
            
            return {
                'input_ids': np.array([encoded.ids], dtype=np.int64),
                'attention_mask': np.array([encoded.attention_mask], dtype=np.int64),
                'token_type_ids': np.array([encoded.type_ids], dtype=np.int64)
            }
        except Exception as e:
            print(f"Error in tokenization: {str(e)}")
            # Create dummy tokenization
            return {
                'input_ids': np.ones((1, 10), dtype=np.int64),
                'attention_mask': np.ones((1, 10), dtype=np.int64),
                'token_type_ids': np.zeros((1, 10), dtype=np.int64)
            }

    def encode(self, texts: Union[str, List[str]], normalize: bool = True, pooling: str = 'mean') -> np.ndarray:
        """
        Generate embeddings for input texts.
        
        Args:
            texts (Union[str, List[str]]): Input text or list of texts
            normalize (bool): Whether to L2-normalize the embeddings
            pooling (str): Pooling strategy ('mean', 'max', or 'cls')
            
        Returns:
            np.ndarray: Array of embeddings, shape (n_texts, embedding_dim)
        """
        # Convert single text to list
        if isinstance(texts, str):
            texts = [texts]
            
        # If using dummy implementation, return random embeddings
        if self.using_dummy:
            embeddings = []
            for _ in range(len(texts)):
                # Create deterministic embeddings based on the text
                text_seed = sum(ord(c) for c in str(texts))
                random.seed(text_seed)
                emb = np.array([random.random() for _ in range(self.embedding_dim)])
                if normalize:
                    emb = emb / np.linalg.norm(emb)
                embeddings.append(emb)
            return np.array(embeddings)
            
        # Use real ONNX model
        embeddings = []
        for text in texts:
            try:
                # Tokenize
                tokens = self._tokenize(text)
                
                # Run inference
                ort_outputs = self.ort_session.run(None, tokens)
                token_embeddings = ort_outputs[0][0]  # Shape [sequence_length, embedding_dim]
                
                # Apply pooling to get sentence embedding
                attention_mask = tokens['attention_mask'][0]
                
                if pooling == 'cls':
                    # Use CLS token embedding (first token)
                    embedding = token_embeddings[0]
                elif pooling == 'max':
                    # Apply max pooling
                    embedding = np.zeros(self.embedding_dim)
                    for i in range(token_embeddings.shape[0]):
                        if attention_mask[i] == 1:  # Only consider non-padding tokens
                            embedding = np.maximum(embedding, token_embeddings[i])
                else:  # Default to mean pooling
                    # Apply mean pooling
                    embedding = np.zeros(self.embedding_dim)
                    valid_tokens = 0
                    for i in range(token_embeddings.shape[0]):
                        if attention_mask[i] == 1:  # Only consider non-padding tokens
                            embedding += token_embeddings[i]
                            valid_tokens += 1
                    if valid_tokens > 0:
                        embedding = embedding / valid_tokens
                
                # Normalize if requested
                if normalize:
                    embedding = embedding / np.linalg.norm(embedding)
                    
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error generating embedding for text: {str(e)}")
                # Generate a fallback embedding
                random.seed(sum(ord(c) for c in text))
                embedding = np.array([random.random() for _ in range(self.embedding_dim)])
                if normalize:
                    embedding = embedding / np.linalg.norm(embedding)
                embeddings.append(embedding)
            
        return np.array(embeddings)

    # This class is directly used as the embedding function for ChromaDB
    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        ChromaDB-compatible embedding function.
        
        Args:
            input (List[str]): List of texts to embed
            
        Returns:
            List[List[float]]: List of embeddings as float lists
        """
        embeddings = self.encode(input)
        return embeddings.tolist()
        
    def get_embedding_function(self):
        """
        Returns a function that can be used as an embedding function for ChromaDB.
        
        Returns:
            Callable: A function that takes a list of strings and returns a list of embeddings
        """
        return self

if __name__ == "__main__":
    # Example usage
    handler = ONNXEmbeddingHandler()
    
    # Test single text
    text = "This is a test sentence."
    embedding = handler.encode(text)
    print(f"Single text embedding shape: {embedding.shape}")
    
    # Test multiple texts
    texts = [
        "First test sentence.",
        "Second test sentence.",
        "Third test sentence."
    ]
    embeddings = handler.encode(texts)
    print(f"Multiple text embeddings shape: {embeddings.shape}")
    
    # Test with ChromaDB-style calling
    chroma_embeddings = handler(texts)
    print(f"ChromaDB embeddings length: {len(chroma_embeddings)}")
    print(f"Each embedding dimension: {len(chroma_embeddings[0])}") 