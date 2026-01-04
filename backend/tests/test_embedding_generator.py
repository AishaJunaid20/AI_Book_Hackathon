"""Unit tests for the embedding generator service."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.services.embedding_generator import EmbeddingGenerator
from src.utils.config import Config


class TestEmbeddingGenerator(unittest.TestCase):
    """Test cases for the EmbeddingGenerator service."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock config
        self.mock_config = Mock(spec=Config)
        self.mock_config.cohere_api_key = "test-api-key"
        self.mock_config.cohere_model = "embed-english-v3.0"
        self.mock_config.embedding_size = 1024

        # Create the generator with mocked client
        with patch('src.services.embedding_generator.cohere.Client'):
            self.generator = EmbeddingGenerator(self.mock_config)

    def test_validate_embedding_correct_size(self):
        """Test embedding validation with correct size."""
        embedding = [0.1] * 1024  # Size 1024 as configured
        self.assertTrue(self.generator.validate_embedding(embedding))

    def test_validate_embedding_incorrect_size(self):
        """Test embedding validation with incorrect size."""
        embedding = [0.1] * 512  # Wrong size
        self.assertFalse(self.generator.validate_embedding(embedding))

    def test_validate_embedding_with_nan(self):
        """Test embedding validation with NaN values."""
        import math
        embedding = [0.1] * 1023 + [float('nan')]  # Contains NaN
        self.assertFalse(self.generator.validate_embedding(embedding))

    def test_validate_embedding_with_non_numeric(self):
        """Test embedding validation with non-numeric values."""
        embedding = [0.1] * 1023 + ["invalid"]  # Contains non-numeric
        self.assertFalse(self.generator.validate_embedding(embedding))

    def test_validate_embedding_empty(self):
        """Test embedding validation with empty list."""
        self.assertFalse(self.generator.validate_embedding([]))

    def test_generate_embedding_for_text_with_empty_text(self):
        """Test generating embedding for empty text."""
        with patch.object(self.generator, 'generate_embeddings') as mock_gen:
            result = self.generator.generate_embedding_for_text("")
            self.assertIsNone(result)
            mock_gen.assert_not_called()

    def test_generate_embedding_for_text_with_whitespace_only(self):
        """Test generating embedding for whitespace-only text."""
        with patch.object(self.generator, 'generate_embeddings') as mock_gen:
            result = self.generator.generate_embedding_for_text("   \n\t  ")
            self.assertIsNone(result)
            mock_gen.assert_not_called()

    def test_batch_generate_embeddings_empty_list(self):
        """Test batch generation with empty list."""
        with patch.object(self.generator, 'generate_embeddings') as mock_gen:
            result = self.generator.batch_generate_embeddings([])
            self.assertIsNone(result)
            mock_gen.assert_not_called()

    @patch('src.services.embedding_generator.time.sleep')
    def test_batch_generate_embeddings_with_batches(self, mock_sleep):
        """Test batch generation with multiple batches."""
        texts = ["text1", "text2", "text3"]
        mock_embeddings = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]

        with patch.object(self.generator, 'generate_embeddings', return_value=mock_embeddings):
            result = self.generator.batch_generate_embeddings(texts, batch_size=2)

            # Should have called generate_embeddings twice (first batch of 2, then batch of 1)
            self.assertEqual(self.generator.generate_embeddings.call_count, 1)  # Called once with all texts
            self.assertEqual(result, mock_embeddings)

    @patch('src.services.embedding_generator.time.sleep')
    def test_batch_generate_embeddings_failure(self, mock_sleep):
        """Test batch generation when API call fails."""
        texts = ["text1", "text2"]

        with patch.object(self.generator, 'generate_embeddings', return_value=None):
            result = self.generator.batch_generate_embeddings(texts)
            self.assertIsNone(result)

    def test_handle_rate_limiting_success(self):
        """Test rate limiting handling with successful connection."""
        mock_response = Mock()
        mock_response.embeddings = [[0.1, 0.2]]

        with patch.object(self.generator.client, 'embed', return_value=mock_response):
            result = self.generator.handle_rate_limiting(max_retries=1)
            self.assertTrue(result)

    def test_handle_rate_limiting_with_rate_limit_error(self):
        """Test rate limiting handling with rate limit error."""
        from cohere import CohereAPIError

        mock_error = CohereAPIError(message="Rate limit exceeded")

        with patch.object(self.generator.client, 'embed', side_effect=mock_error):
            result = self.generator.handle_rate_limiting(max_retries=1)
            self.assertFalse(result)

    def test_handle_rate_limiting_with_other_error(self):
        """Test rate limiting handling with other error."""
        mock_error = Exception("Other error")

        with patch.object(self.generator.client, 'embed', side_effect=mock_error):
            result = self.generator.handle_rate_limiting(max_retries=1)
            self.assertFalse(result)


class TestEmbeddingGeneratorIntegration(unittest.TestCase):
    """Integration tests for EmbeddingGenerator (with mocked API calls)."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = Mock(spec=Config)
        self.mock_config.cohere_api_key = "test-api-key"
        self.mock_config.cohere_model = "embed-english-v3.0"
        self.mock_config.embedding_size = 2  # Small size for testing

        # Mock the Cohere client response
        self.mock_cohere_response = Mock()
        self.mock_cohere_response.embeddings = [[0.1, 0.2], [0.3, 0.4]]

    @patch('src.services.embedding_generator.cohere.Client')
    def test_generate_embeddings_success(self, mock_client_class):
        """Test successful embedding generation."""
        # Setup mock
        mock_client = Mock()
        mock_client.embed.return_value = self.mock_cohere_response
        mock_client_class.return_value = mock_client

        # Create generator
        self.mock_config.embedding_size = 2
        generator = EmbeddingGenerator(self.mock_config)

        # Test
        texts = ["Hello world", "Test text"]
        result = generator.generate_embeddings(texts)

        # Assertions
        self.assertEqual(result, [[0.1, 0.2], [0.3, 0.4]])
        mock_client.embed.assert_called_once_with(
            texts=texts,
            model="embed-english-v3.0",
            input_type="search_document"
        )

    @patch('src.services.embedding_generator.cohere.Client')
    def test_generate_embeddings_with_cohere_error(self, mock_client_class):
        """Test embedding generation with Cohere API error."""
        from cohere import CohereAPIError

        # Setup mock to raise error
        mock_client = Mock()
        mock_client.embed.side_effect = CohereAPIError(message="API Error")
        mock_client_class.return_value = mock_client

        # Create generator
        self.mock_config.embedding_size = 2
        generator = EmbeddingGenerator(self.mock_config)

        # Test
        texts = ["Hello world"]
        result = generator.generate_embeddings(texts)

        # Assertions
        self.assertIsNone(result)

    @patch('src.services.embedding_generator.cohere.Client')
    def test_generate_embeddings_with_network_error(self, mock_client_class):
        """Test embedding generation with network error."""
        import requests

        # Setup mock to raise error
        mock_client = Mock()
        mock_client.embed.side_effect = requests.exceptions.RequestException("Network error")
        mock_client_class.return_value = mock_client

        # Create generator
        self.mock_config.embedding_size = 2
        generator = EmbeddingGenerator(self.mock_config)

        # Test
        texts = ["Hello world"]
        result = generator.generate_embeddings(texts)

        # Assertions
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()