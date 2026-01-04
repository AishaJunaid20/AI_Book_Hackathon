"""Service for interacting with Qdrant vector database."""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Any, Optional
import logging
import time
from uuid import uuid4
from ..utils.config import Config


class QdrantService:
    """Service to interact with Qdrant vector database."""

    def __init__(self, config: Config, max_retries: int = 3):
        """Initialize the Qdrant service with configuration."""
        self.config = config
        self.url = config.qdrant_url
        self.api_key = config.qdrant_api_key
        self.collection_name = config.qdrant_collection_name
        self.vector_size = config.embedding_size
        self.max_retries = max_retries

        # Initialize Qdrant client
        if self.url and self.api_key:
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=10
            )
        else:
            # For local development without cloud
            self.client = QdrantClient(":memory:")  # In-memory for testing without cloud access

        self._ensure_collection_exists()

    def _execute_with_retry(self, operation, *args, **kwargs):
        """Execute an operation with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logging.warning(f"Qdrant operation failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Qdrant operation failed after {self.max_retries} attempts: {e}")

        raise last_exception

    def _ensure_collection_exists(self):
        """Ensure the collection exists with the correct configuration."""
        def _create_collection():
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection if it doesn't exist
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                logging.info(f"Created collection: {self.collection_name}")
            else:
                logging.info(f"Collection {self.collection_name} already exists")

        self._execute_with_retry(_create_collection)

    def store_embedding(self, text: str, embedding: List[float], metadata: Dict[str, Any] = None) -> str:
        """Store a single embedding in Qdrant."""
        def _store():
            # Generate a unique ID for the record
            record_id = str(uuid4())

            # Prepare the payload with text and metadata
            payload = {
                'text': text,
                'created_at': str(self._get_current_timestamp())
            }

            if metadata:
                payload.update(metadata)

            # Store the record in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=record_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )

            return record_id

        return self._execute_with_retry(_store)

    def store_embeddings_batch(self, texts: List[str], embeddings: List[List[float]],
                              metadata_list: List[Dict[str, Any]] = None) -> List[str]:
        """Store multiple embeddings in Qdrant."""
        def _store_batch():
            record_ids = []

            # Prepare points for batch upload
            points = []
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                record_id = str(uuid4())
                record_ids.append(record_id)

                payload = {
                    'text': text,
                    'created_at': str(self._get_current_timestamp())
                }

                if metadata_list and i < len(metadata_list):
                    payload.update(metadata_list[i])

                points.append(models.PointStruct(
                    id=record_id,
                    vector=embedding,
                    payload=payload
                ))

            # Upload points to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            return record_ids

        return self._execute_with_retry(_store_batch)

    def retrieve_embedding(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single embedding by ID."""
        def _retrieve():
            records = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[record_id]
            )

            if records:
                record = records[0]
                return {
                    'id': str(record.id),
                    'vector': record.vector,
                    'payload': record.payload
                }
            return None

        try:
            return self._execute_with_retry(_retrieve)
        except Exception as e:
            logging.error(f"Error retrieving embedding: {e}")
            return None

    def search_similar(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar embeddings using vector similarity."""
        def _search():
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )

            search_results = []
            for result in results:
                search_results.append({
                    'id': str(result.id),
                    'score': result.score,
                    'payload': result.payload,
                    'text': result.payload.get('text', '')
                })

            return search_results

        try:
            return self._execute_with_retry(_search)
        except Exception as e:
            logging.error(f"Error searching for similar embeddings: {e}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        def _get_info():
            collection_info = self.client.get_collection(self.collection_name)
            return {
                'name': self.collection_name,
                'vector_size': collection_info.config.params.vectors.size,
                'distance': collection_info.config.params.vectors.distance,
                'points_count': collection_info.points_count
            }

        try:
            return self._execute_with_retry(_get_info)
        except Exception as e:
            logging.error(f"Error getting collection info: {e}")
            return {}

    def delete_embedding(self, record_id: str) -> bool:
        """Delete a single embedding by ID."""
        def _delete():
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[record_id]
                )
            )
            return True

        try:
            return self._execute_with_retry(_delete)
        except Exception as e:
            logging.error(f"Error deleting embedding: {e}")
            return False

    def _get_current_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow()

    def health_check(self) -> bool:
        """Check if the Qdrant service is accessible."""
        def _health_check():
            # Try to get collection info as a basic health check
            self.client.get_collection(self.collection_name)
            return True

        try:
            return self._execute_with_retry(_health_check)
        except Exception:
            return False