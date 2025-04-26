import os
import numpy as np
import json

def create_dummy_model():
    """
    Creates a dummy model file for testing when the real model can't be downloaded.
    This isn't a real ONNX model but will prevent errors when the file is missing.
    """
    # Use relative paths within the current directory for local testing
    model_dir = "onnx-models/all-MiniLM-L6-v2-onnx"
    
    # Create model directory
    os.makedirs(model_dir, exist_ok=True)
    
    # Create a dummy embedding model
    dummy_embedding = np.random.rand(384).astype(np.float32)
    
    # Save as a simple binary file
    model_path = os.path.join(model_dir, "model.onnx")
    with open(model_path, 'wb') as f:
        f.write(b'DUMMY_ONNX_MODEL')
        np.save(f, dummy_embedding)
    
    print(f"Created dummy model at {model_path}")
    
    # Create metadata file
    metadata = {
        "dimension": 384,
        "dummy": True,
        "created": "fallback_for_testing"
    }
    
    metadata_path = os.path.join(model_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)
    
    print(f"Created metadata at {metadata_path}")
    return True

if __name__ == "__main__":
    print("Creating dummy ONNX model for testing...")
    create_dummy_model()
    print("Done!") 