"""Configuration management for the embeddings generation service."""

import os
import yaml
from typing import Dict, Any


class Config:
    """Configuration class to manage application settings."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration from YAML file and environment variables."""
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file and override with environment variables."""
        config = {}

        # Load from YAML file if it exists
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

        # Override with environment variables where specified
        # Cohere configuration
        cohere_api_key = os.getenv('COHERE_API_KEY')
        if cohere_api_key:
            if 'cohere' not in config:
                config['cohere'] = {}
            config['cohere']['api_key'] = cohere_api_key

        # Qdrant configuration
        qdrant_url = os.getenv('QDRANT_URL')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        qdrant_collection_name = os.getenv('QDRANT_COLLECTION_NAME')

        if 'qdrant' not in config:
            config['qdrant'] = {}

        if qdrant_url:
            config['qdrant']['url'] = qdrant_url
        if qdrant_api_key:
            config['qdrant']['api_key'] = qdrant_api_key
        if qdrant_collection_name:
            config['qdrant']['collection_name'] = qdrant_collection_name

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'cohere.api_key')."""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @property
    def cohere_api_key(self) -> str:
        """Get Cohere API key."""
        return self.get('cohere.api_key', '')

    @property
    def cohere_model(self) -> str:
        """Get Cohere model name."""
        return self.get('cohere.model', 'embed-english-v3.0')

    @property
    def qdrant_url(self) -> str:
        """Get Qdrant URL."""
        return self.get('qdrant.url', '')

    @property
    def qdrant_api_key(self) -> str:
        """Get Qdrant API key."""
        return self.get('qdrant.api_key', '')

    @property
    def qdrant_collection_name(self) -> str:
        """Get Qdrant collection name."""
        return self.get('qdrant.collection_name', 'book_embeddings')

    @property
    def chunk_size(self) -> int:
        """Get chunk size for content processing."""
        return self.get('processing.chunk_size', 1000)

    @property
    def embedding_size(self) -> int:
        """Get embedding vector size."""
        return self.get('cohere.embedding_size', 1024)