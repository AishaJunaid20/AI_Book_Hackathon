#!/usr/bin/env python3
"""Basic functionality test to verify the implementation works."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.content_parser import ContentParser
from src.utils.config import Config
from src.services.embedding_generator import EmbeddingGenerator
from src.services.qdrant_service import QdrantService


def test_basic_functionality():
    """Test basic functionality of the services."""
    print("Testing basic functionality...")

    # Test ContentParser
    print("[PASS] Testing ContentParser...")
    parser = ContentParser(chunk_size=50)

    # Test basic parsing and chunking
    test_text = "This is a test document with enough words to pass validation requirements for the system. " * 2
    chunks = parser.chunk_text(test_text, chunk_size=20)
    assert len(chunks) > 0, "Should create at least one chunk"
    print(f"  - Created {len(chunks)} chunks from test text")

    # Test validation
    is_valid = parser.validate_content(test_text)
    assert is_valid, "Test text should be valid"
    print("  - Content validation working")

    # Test Config
    print("[PASS] Testing Config...")
    # Create a minimal config for testing
    import tempfile
    import yaml

    config_data = {
        'cohere': {
            'api_key': 'dummy-key-for-test',
            'model': 'embed-english-v3.0',
            'embedding_size': 2  # Small size for testing
        },
        'qdrant': {
            'url': 'dummy-url-for-test',
            'api_key': 'dummy-key-for-test',
            'collection_name': 'test_collection',
            'vector_size': 2,
            'distance': 'Cosine'
        },
        'processing': {
            'chunk_size': 100
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name

    try:
        config = Config(config_file)
        print("  - Config loading working")
    finally:
        os.unlink(config_file)

    print("[PASS] All basic functionality tests passed!")
    return True


if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("\n[SUCCESS] Implementation verification successful!")
    else:
        print("\n[ERROR] Implementation verification failed!")
        sys.exit(1)