import numpy as np
from embedding_handler import ONNXEmbeddingHandler

def test_embedding_handler():
    """Test the ONNXEmbeddingHandler functionality"""
    print("\n=== Testing ONNX Embedding Handler ===")
    
    # Initialize the embedding handler
    handler = ONNXEmbeddingHandler()
    
    # Single text embedding
    text = "Turn on the engine"
    embedding = handler.encode(text)
    print(f"Single text: '{text}'")
    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding norm: {np.linalg.norm(embedding[0])}")
    
    # Multiple texts embeddings
    texts = [
        "Lock the doors",
        "Unlock the doors",
        "Turn on the headlights",
        "Open the window"
    ]
    print(f"\nMultiple texts ({len(texts)}):")
    for t in texts:
        print(f"  - '{t}'")
        
    embeddings = handler.encode(texts)
    print(f"Embeddings shape: {embeddings.shape}")
    
    # Similarity test
    print("\nSimilarity Tests:")
    
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    query1 = handler.encode("Close the doors")[0]  # Now a vector of shape (embedding_dim,)
    query2 = handler.encode("Turn off the lights")[0]
    
    for i, text in enumerate(texts):
        emb = embeddings[i]  # Now a vector of shape (embedding_dim,)
        sim1 = cosine_similarity(query1, emb)
        sim2 = cosine_similarity(query2, emb)
        print(f"'{text}':")
        print(f"  - Similarity to 'Close the doors': {sim1:.4f}")
        print(f"  - Similarity to 'Turn off the lights': {sim2:.4f}")
    
    # Test different pooling strategies
    print("\nPooling Strategy Tests:")
    text = "Test different pooling strategies"
    
    mean_emb = handler.encode(text, pooling='mean')[0]
    max_emb = handler.encode(text, pooling='max')[0]
    cls_emb = handler.encode(text, pooling='cls')[0]
    
    print(f"Mean pooling embedding norm: {np.linalg.norm(mean_emb):.4f}")
    print(f"Max pooling embedding norm: {np.linalg.norm(max_emb):.4f}")
    print(f"CLS token embedding norm: {np.linalg.norm(cls_emb):.4f}")
    
    # Test ChromaDB function
    print("\nChromaDB embedding function test:")
    embedding_function = handler.get_embedding_function()
    result = embedding_function(["Test the embedding function"])
    print(f"Result type: {type(result)}")
    print(f"Result length: {len(result)}")
    print(f"Embedding dimension: {len(result[0])}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    print("ONNX Embedding Test Suite")
    print("========================")
    
    test_embedding_handler() 