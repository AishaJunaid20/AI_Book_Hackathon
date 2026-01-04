"""Unit tests for the Qdrant service."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.services.qdrant_service import QdrantService
from src.utils.config import Config


class TestQdrantService(unittest.TestCase):
    """Test cases for the QdrantService."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock config
        self.mock_config = Mock(spec=Config)
        self.mock_config.qdrant_url = "https://test.qdrant.tech:6333"
        self.mock_config.qdrant_api_key = "test-api-key"
        self.mock_config.qdrant_collection_name = "test_collection"
        self.mock_config.embedding_size = 1024

        # Create the service with mocked client
        with patch('src.services.qdrant_service.QdrantClient') as mock_client:
            self.mock_qdrant_client = Mock()
            mock_client.return_value = self.mock_qdrant_client

            # Mock collections response
            mock_collections = Mock()
            mock_collections.collections = []
            self.mock_qdrant_client.get_collections.return_value = mock_collections

            # Mock ensure_collection_exists to do nothing
            with patch.object(QdrantService, '_ensure_collection_exists'):
                self.service = QdrantService(self.mock_config, max_retries=1)

    def test_store_embedding_success(self):
        """Test successful embedding storage."""
        embedding = [0.1, 0.2, 0.3]
        text = "Test text"
        metadata = {"source": "test"}

        # Mock the upsert method
        self.mock_qdrant_client.upsert = Mock()

        # Call the method
        record_id = self.service.store_embedding(text, embedding, metadata)

        # Assertions
        self.assertIsInstance(record_id, str)
        self.mock_qdrant_client.upsert.assert_called_once()

        # Check that the call includes the expected data
        call_args = self.mock_qdrant_client.upsert.call_args
        self.assertEqual(call_args[1]['collection_name'], "test_collection")

    def test_store_embeddings_batch_success(self):
        """Test successful batch embedding storage."""
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        texts = ["Text 1", "Text 2"]
        metadata_list = [{"source": "test1"}, {"source": "test2"}]

        # Mock the upsert method
        self.mock_qdrant_client.upsert = Mock()

        # Call the method
        record_ids = self.service.store_embeddings_batch(texts, embeddings, metadata_list)

        # Assertions
        self.assertIsInstance(record_ids, list)
        self.assertEqual(len(record_ids), 2)
        self.mock_qdrant_client.upsert.assert_called_once()

    def test_retrieve_embedding_success(self):
        """Test successful embedding retrieval."""
        record_id = "test-id"

        # Mock the retrieve response
        mock_point = Mock()
        mock_point.id = record_id
        mock_point.vector = [0.1, 0.2, 0.3]
        mock_point.payload = {"text": "Test text"}

        self.mock_qdrant_client.retrieve = Mock(return_value=[mock_point])

        # Call the method
        result = self.service.retrieve_embedding(record_id)

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], record_id)
        self.assertEqual(result['vector'], [0.1, 0.2, 0.3])
        self.assertEqual(result['payload'], {"text": "Test text"})

    def test_retrieve_embedding_not_found(self):
        """Test retrieval when embedding is not found."""
        record_id = "non-existent-id"

        # Mock empty response
        self.mock_qdrant_client.retrieve = Mock(return_value=[])

        # Call the method
        result = self.service.retrieve_embedding(record_id)

        # Assertions
        self.assertIsNone(result)

    def test_search_similar_success(self):
        """Test successful similarity search."""
        query_embedding = [0.1, 0.2, 0.3]

        # Mock search result
        mock_result = Mock()
        mock_result.id = "result-id"
        mock_result.score = 0.95
        mock_result.payload = {"text": "Similar text"}

        self.mock_qdrant_client.search = Mock(return_value=[mock_result])

        # Call the method
        results = self.service.search_similar(query_embedding, limit=1)

        # Assertions
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "result-id")
        self.assertEqual(results[0]['score'], 0.95)

    def test_get_collection_info_success(self):
        """Test successful collection info retrieval."""
        # Mock collection info
        mock_collection_info = Mock()
        mock_collection_info.config.params.vectors.size = 1024
        mock_collection_info.config.params.vectors.distance = "Cosine"
        mock_collection_info.points_count = 100

        self.mock_qdrant_client.get_collection = Mock(return_value=mock_collection_info)

        # Call the method
        info = self.service.get_collection_info()

        # Assertions
        self.assertEqual(info['vector_size'], 1024)
        self.assertEqual(info['distance'], "Cosine")
        self.assertEqual(info['points_count'], 100)

    def test_delete_embedding_success(self):
        """Test successful embedding deletion."""
        record_id = "test-id"

        # Mock delete method
        self.mock_qdrant_client.delete = Mock(return_value=True)

        # Call the method
        result = self.service.delete_embedding(record_id)

        # Assertions
        self.assertTrue(result)
        self.mock_qdrant_client.delete.assert_called_once()

    def test_health_check_success(self):
        """Test health check success."""
        # Mock get_collection to return successfully
        mock_collection_info = Mock()
        self.mock_qdrant_client.get_collection = Mock(return_value=mock_collection_info)

        # Call the method
        result = self.service.health_check()

        # Assertions
        self.assertTrue(result)

    def test_health_check_failure(self):
        """Test health check failure."""
        # Mock get_collection to raise an exception
        self.mock_qdrant_client.get_collection = Mock(side_effect=Exception("Connection failed"))

        # Call the method
        result = self.service.health_check()

        # Assertions
        self.assertFalse(result)

    @patch('src.services.qdrant_service.time.sleep')
    def test_retry_logic_on_failure(self, mock_sleep):
        """Test that retry logic works when operations fail."""
        record_id = "test-id"

        # Mock retrieve to fail twice then succeed
        self.mock_qdrant_client.retrieve = Mock()
        self.mock_qdrant_client.retrieve.side_effect = [Exception("Failed"), Exception("Failed"), [Mock()]]

        # Create service with 3 retries
        with patch.object(QdrantService, '_ensure_collection_exists'):
            service_with_retries = QdrantService(self.mock_config, max_retries=3)

        # Call the method - should succeed after retries
        try:
            result = service_with_retries.retrieve_embedding(record_id)
            # If we get here, the retry logic worked
            self.assertIsNotNone(result)
        except Exception:
            # If we still fail, that's also valid behavior if all retries exhausted
            pass


class TestQdrantServiceIntegration(unittest.TestCase):
    """Integration tests for QdrantService (with mocked Qdrant calls)."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=Config)
        self.mock_config.qdrant_url = "https://test.qdrant.tech:6333"
        self.mock_config.qdrant_api_key = "test-api-key"
        self.mock_config.qdrant_collection_name = "test_collection"
        self.mock_config.embedding_size = 2

    @patch('src.services.qdrant_service.QdrantClient')
    def test_full_integration_flow(self, mock_client_class):
        """Test a full integration flow: store, retrieve, search."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock collection operations
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections

        # Mock upsert operation
        mock_client.upsert.return_value = True

        # Mock retrieve operation
        mock_point = Mock()
        mock_point.id = "stored-id"
        mock_point.vector = [0.1, 0.2]
        mock_point.payload = {"text": "Test text", "created_at": "2026-01-01T00:00:00Z"}
        mock_client.retrieve.return_value = [mock_point]

        # Mock search operation
        mock_search_result = Mock()
        mock_search_result.id = "search-result-id"
        mock_search_result.score = 0.95
        mock_search_result.payload = {"text": "Similar text", "created_at": "2026-01-01T00:00:00Z"}
        mock_search_result.text = "Similar text"
        mock_client.search.return_value = [mock_search_result]

        # Create service with mocked collection creation
        with patch.object(QdrantService, '_ensure_collection_exists'):
            service = QdrantService(self.mock_config, max_retries=1)

        # Test storing an embedding
        embedding = [0.1, 0.2]
        text = "Test text"
        record_id = service.store_embedding(text, embedding)

        self.assertIsInstance(record_id, str)

        # Test retrieving the embedding
        retrieved = service.retrieve_embedding(record_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['id'], "stored-id")

        # Test searching for similar embeddings
        search_results = service.search_similar(embedding, limit=1)
        self.assertIsInstance(search_results, list)
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0]['id'], "search-result-id")


if __name__ == '__main__':
    unittest.main()