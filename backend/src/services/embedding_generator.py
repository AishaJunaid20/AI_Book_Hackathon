"""Service for generating embeddings using Cohere API."""

import cohere
from typing import List, Dict, Any, Optional
import time
import logging
import requests
from ..utils.config import Config


class EmbeddingGenerator:
    """Service to generate embeddings using Cohere API."""

    def __init__(self, config: Config):
        """Initialize the embedding generator with configuration."""
        self.config = config
        self.api_key = config.cohere_api_key
        self.model = config.cohere_model
        self.client = cohere.Client(self.api_key)
        self.embedding_size = config.embedding_size

    def generate_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            logging.warning("No texts provided for embedding generation")
            return None

        try:
            # Call Cohere API to generate embeddings
            response = self.client.embed(
                texts=texts,
                model=self.model,
                input_type="search_document"  # Using search_document as default input type
            )

            return response.embeddings
        except cohere.CohereAPIError as e:
            logging.error(f"Cohere API error: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error during embedding generation: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during embedding generation: {e}")
            return None

    def generate_embedding_for_text(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            logging.warning("Empty text provided for embedding generation")
            return None

        embeddings = self.generate_embeddings([text])
        if embeddings and len(embeddings) > 0:
            return embeddings[0]
        return None

    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate that an embedding has the correct size and format."""
        if not embedding or len(embedding) != self.embedding_size:
            return False

        # Check that all values are valid floats
        for value in embedding:
            if not isinstance(value, (int, float)) or value != value:  # Check for NaN
                return False

        return True

    def batch_generate_embeddings(self, texts: List[str], batch_size: int = 96) -> Optional[List[List[float]]]:
        """Generate embeddings in batches to handle large inputs."""
        if not texts:
            logging.warning("No texts provided for batch embedding generation")
            return None

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.generate_embeddings(batch)

            if batch_embeddings is None:
                logging.error(f"Failed to generate embeddings for batch starting at index {i}")
                return None

            all_embeddings.extend(batch_embeddings)

            # Add a small delay to respect rate limits
            time.sleep(0.1)

        return all_embeddings

    def handle_rate_limiting(self, max_retries: int = 3) -> bool:
        """Handle rate limiting by implementing exponential backoff."""
        for attempt in range(max_retries):
            try:
                # Test the API connection
                response = self.client.embed(
                    texts=["test"],
                    model=self.model,
                    input_type="search_document"
                )
                return True
            except cohere.CohereAPIError as e:
                if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logging.info(f"Rate limited, waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Failed to connect to Cohere API after {max_retries} attempts: {e}")
                    return False
            except Exception as e:
                logging.error(f"Unexpected error during rate limit handling: {e}")
                return False

        return False