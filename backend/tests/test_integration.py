"""Integration tests for the complete embeddings generation workflow."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.services.content_parser import ContentParser
from src.services.embedding_generator import EmbeddingGenerator
from src.services.qdrant_service import QdrantService
from src.utils.config import Config


class TestIntegrationWorkflow(unittest.TestCase):
    """Integration tests for the complete workflow: URL → content → embeddings → storage."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock config
        self.mock_config = Mock(spec=Config)
        self.mock_config.cohere_api_key = "test-api-key"
        self.mock_config.cohere_model = "embed-english-v3.0"
        self.mock_config.embedding_size = 1024
        self.mock_config.qdrant_url = "https://test.qdrant.tech:6333"
        self.mock_config.qdrant_api_key = "test-api-key"
        self.mock_config.qdrant_collection_name = "test_collection"
        self.mock_config.chunk_size = 100

    @patch('src.services.qdrant_service.QdrantClient')
    @patch('src.services.embedding_generator.cohere.Client')
    def test_complete_workflow_success(self, mock_cohere_client, mock_qdrant_client):
        """Test the complete workflow from content parsing to storage."""
        # Setup mocked services
        mock_cohere_response = Mock()
        mock_cohere_response.embeddings = [[0.1, 0.2, 0.3, 0.4] * 256]  # 1024-dim vector
        mock_cohere_client.return_value.embed.return_value = mock_cohere_response

        mock_qdrant = Mock()
        mock_qdrant_client.return_value = mock_qdrant

        # Mock collections response
        mock_collections = Mock()
        mock_collections.collections = []
        mock_qdrant.get_collections.return_value = mock_collections

        # Mock upsert operation
        mock_qdrant.upsert.return_value = True

        # Create services
        content_parser = ContentParser(chunk_size=50)  # Small chunk size for testing
        embedding_generator = EmbeddingGenerator(self.mock_config)
        qdrant_service = QdrantService(self.mock_config, max_retries=1)

        # Test content
        test_content = "This is a test document with enough words to create multiple chunks for testing purposes. " * 3

        # Step 1: Parse and chunk content
        chunks = content_parser.chunk_text(test_content, chunk_size=10)  # Use smaller chunk size to ensure multiple chunks
        self.assertGreater(len(chunks), 1, "Content should be chunked into multiple parts")

        # Step 2: Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = embedding_generator.batch_generate_embeddings(texts)

        self.assertIsNotNone(embeddings, "Embeddings should be generated")
        self.assertEqual(len(embeddings), len(texts), "Should have embeddings for each text chunk")
        self.assertEqual(len(embeddings[0]), 1024, "Each embedding should have correct dimension")

        # Step 3: Store embeddings in Qdrant
        metadata_list = [{'chunk_index': i, 'source': 'test'} for i in range(len(chunks))]
        record_ids = qdrant_service.store_embeddings_batch(texts, embeddings, metadata_list)

        self.assertIsNotNone(record_ids, "Record IDs should be returned")
        self.assertEqual(len(record_ids), len(texts), "Should have IDs for each embedding")

    @patch('src.services.qdrant_service.QdrantClient')
    @patch('src.services.embedding_generator.cohere.Client')
    def test_complete_workflow_with_realistic_content(self, mock_cohere_client, mock_qdrant_client):
        """Test the complete workflow with more realistic content."""
        # Setup mocked services
        # Generate multiple embeddings for multiple chunks
        mock_cohere_response = Mock()
        mock_cohere_response.embeddings = [
            [0.1 + i * 0.01] * 1024 for i in range(5)  # 5 embeddings of 1024 dimensions
        ]
        mock_cohere_client.return_value.embed.return_value = mock_cohere_response

        mock_qdrant = Mock()
        mock_qdrant_client.return_value = mock_qdrant

        # Mock collections response
        mock_collections = Mock()
        mock_collections.collections = []
        mock_qdrant.get_collections.return_value = mock_collections

        # Mock upsert operation
        mock_qdrant.upsert.return_value = True

        # Mock retrieve operation
        mock_point = Mock()
        mock_point.id = "test-id"
        mock_point.vector = [0.1] * 1024
        mock_point.payload = {"text": "test text", "chunk_index": 0, "source": "test"}
        mock_qdrant.retrieve.return_value = [mock_point]

        # Create services
        content_parser = ContentParser(chunk_size=100)
        embedding_generator = EmbeddingGenerator(self.mock_config)
        qdrant_service = QdrantService(self.mock_config, max_retries=1)

        # Realistic test content
        test_content = """
        Machine learning is a method of data analysis that automates analytical model building.
        It is a branch of artificial intelligence based on the idea that systems can learn from data,
        identify patterns and make decisions with minimal human intervention. Machine learning algorithms
        are trained using sample data that teaches them to make predictions or identify patterns.
        The algorithms learn from past computations to produce reliable, repeatable decisions and results.

        There are three main types of machine learning: supervised, unsupervised, and reinforcement learning.
        Supervised learning uses labeled data to train algorithms for predicting outcomes for new data.
        Unsupervised learning finds hidden patterns in unlabeled data. Reinforcement learning trains algorithms
        through trial and error using rewards and penalties.

        Deep learning is a subset of machine learning that uses neural networks with multiple layers.
        These neural networks attempt to simulate the behavior of the human brain, though far from matching
        its ability. Deep learning involves massive amounts of data and computational power to process.
        """

        # Process the content
        content_data = content_parser.process_and_chunk_url("https://example.com/test")
        # Since we're not actually fetching from a URL, we'll simulate the processing
        chunks = content_parser.chunk_text(test_content, chunk_size=100)

        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = embedding_generator.batch_generate_embeddings(texts)

        # Store in Qdrant
        metadata_list = [{'chunk_index': i, 'source': 'integration_test', 'text_length': len(text)}
                         for i, text in enumerate(texts)]
        record_ids = qdrant_service.store_embeddings_batch(texts, embeddings, metadata_list)

        # Verify storage
        self.assertEqual(len(record_ids), len(texts))
        self.assertGreater(len(record_ids), 0)

        # Test retrieval
        if record_ids:
            retrieved = qdrant_service.retrieve_embedding(record_ids[0])
            self.assertIsNotNone(retrieved)

    @patch('src.services.qdrant_service.QdrantClient')
    @patch('src.services.embedding_generator.cohere.Client')
    def test_error_handling_in_workflow(self, mock_cohere_client, mock_qdrant_client):
        """Test that errors in one step don't break the entire workflow."""
        # Setup to cause an error in embedding generation
        mock_cohere_client.return_value.embed.side_effect = Exception("API Error")

        # Create services
        content_parser = ContentParser(chunk_size=50)
        embedding_generator = EmbeddingGenerator(self.mock_config)

        # Test content (must have at least 10 words for validation)
        test_content = "This is a test document for error handling with enough words for validation."

        # Parse content
        chunks = content_parser.chunk_text(test_content, chunk_size=50)
        texts = [chunk['text'] for chunk in chunks]

        # Try to generate embeddings - should fail gracefully
        embeddings = embedding_generator.batch_generate_embeddings(texts)
        self.assertIsNone(embeddings, "Should return None when embedding generation fails")

    @patch('src.services.qdrant_service.QdrantClient')
    @patch('src.services.embedding_generator.cohere.Client')
    def test_validation_throughout_workflow(self, mock_cohere_client, mock_qdrant_client):
        """Test that validation happens at each step of the workflow."""
        # Setup mocked services
        mock_cohere_response = Mock()
        mock_cohere_response.embeddings = [[0.1] * 1024]  # 1024-dim vector
        mock_cohere_client.return_value.embed.return_value = mock_cohere_response

        mock_qdrant = Mock()
        mock_qdrant_client.return_value = mock_qdrant

        # Mock collections response
        mock_collections = Mock()
        mock_collections.collections = []
        mock_qdrant.get_collections.return_value = mock_collections

        # Mock upsert operation
        mock_qdrant.upsert.return_value = True

        # Create services
        content_parser = ContentParser(chunk_size=50)
        embedding_generator = EmbeddingGenerator(self.mock_config)
        qdrant_service = QdrantService(self.mock_config, max_retries=1)

        # Test content validation in parser
        valid_content = "This is valid content with sufficient words for testing purposes."
        chunks = content_parser.chunk_text(valid_content, chunk_size=50)
        self.assertGreater(len(chunks), 0, "Should create chunks from valid content")

        # Test embedding validation
        texts = [chunk['text'] for chunk in chunks]
        embeddings = embedding_generator.batch_generate_embeddings(texts)

        # Validate each embedding
        for embedding in embeddings:
            is_valid = embedding_generator.validate_embedding(embedding)
            self.assertTrue(is_valid, f"Embedding should be valid: {len(embedding)} dimensions")


class TestMainWorkflowIntegration(unittest.TestCase):
    """Tests for the main workflow function."""

    @patch('src.services.qdrant_service.QdrantClient')
    @patch('src.services.embedding_generator.cohere.Client')
    def test_process_url_to_embeddings_success(self, mock_cohere_client, mock_qdrant_client):
        """Test the main workflow function end-to-end."""
        from src.main import process_url_to_embeddings

        # Setup mocked services
        mock_cohere_response = Mock()
        mock_cohere_response.embeddings = [[0.1] * 1024]  # 1024-dim vector
        mock_cohere_client.return_value.embed.return_value = mock_cohere_response

        mock_qdrant = Mock()
        mock_qdrant_client.return_value = mock_qdrant

        # Mock collections response
        mock_collections = Mock()
        mock_collections.collections = []
        mock_qdrant.get_collections.return_value = mock_collections

        # Mock upsert operation
        mock_qdrant.upsert.return_value = True

        # Mock content parser to return test data
        with patch('src.main.ContentParser') as mock_content_parser_class:
            mock_content_parser = Mock()
            mock_content_parser.process_and_chunk_url.return_value = {
                'url': 'https://example.com/test',
                'title': 'Test Title',
                'content': 'Test content for integration.',
                'content_type': 'html',
                'word_count': 10,
                'chunks': [{'text': 'Test content for integration.', 'id': 'chunk_0', 'chunk_index': 0, 'word_count': 5}],
                'total_chunks': 1
            }
            mock_content_parser_class.return_value = mock_content_parser

            # Mock config
            mock_config = Mock(spec=Config)
            mock_config.cohere_api_key = "test-api-key"
            mock_config.cohere_model = "embed-english-v3.0"
            mock_config.embedding_size = 1024
            mock_config.qdrant_url = "https://test.qdrant.tech:6333"
            mock_config.qdrant_api_key = "test-api-key"
            mock_config.qdrant_collection_name = "test_collection"
            mock_config.chunk_size = 100

            # Test the main workflow
            result = process_url_to_embeddings("https://example.com/test", mock_config)

            # Should succeed
            self.assertTrue(result, "Main workflow should complete successfully")


if __name__ == '__main__':
    unittest.main()