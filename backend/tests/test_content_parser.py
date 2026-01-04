"""Unit tests for the content parser service."""

import unittest
from unittest.mock import Mock, patch
from src.services.content_parser import ContentParser, count_words


class TestContentParser(unittest.TestCase):
    """Test cases for the ContentParser service."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = ContentParser(timeout=10, chunk_size=100)

    def test_count_words(self):
        """Test word counting function."""
        text = "This is a test sentence with 8 words."
        self.assertEqual(count_words(text), 8)

        # Test with multiple spaces
        text = "This  has   extra    spaces"
        self.assertEqual(count_words(text), 4)

        # Test with empty string
        self.assertEqual(count_words(""), 0)

        # Test with whitespace only
        self.assertEqual(count_words("   \n\t  "), 0)

    def test_validate_content(self):
        """Test content validation."""
        # Valid content
        valid_content = "This is a valid content with more than 10 words for testing purposes."
        self.assertTrue(self.parser.validate_content(valid_content))

        # Empty content
        self.assertFalse(self.parser.validate_content(""))
        self.assertFalse(self.parser.validate_content("   "))

        # Content with less than 10 words
        short_content = "This is only nine words test here"
        self.assertFalse(self.parser.validate_content(short_content))

    def test_sanitize_content(self):
        """Test content sanitization."""
        # Test null byte removal
        dirty_content = "Content with\x00null byte and enough words for validation"
        clean_content = self.parser.sanitize_content(dirty_content)
        self.assertNotIn('\x00', clean_content)

        # Test whitespace normalization
        dirty_content = "Content  with   extra    spaces and enough words for validation"
        clean_content = self.parser.sanitize_content(dirty_content)
        self.assertEqual(clean_content, "Content with extra spaces and enough words for validation")

        # Test newline normalization
        dirty_content = "Content\n\n\nwith\n\nexcessive\n\n\nnewlines and enough words for validation"
        clean_content = self.parser.sanitize_content(dirty_content)
        self.assertEqual(clean_content, "Content\n\nwith\n\nexcessive\n\nnewlines and enough words for validation")

    def test_chunk_text(self):
        """Test text chunking functionality."""
        # Create content with 250 words
        test_words = "word " * 250
        chunks = self.parser.chunk_text(test_words, chunk_size=100)

        # Should have 3 chunks: 100, 100, 50
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0]['word_count'], 100)
        self.assertEqual(chunks[1]['word_count'], 100)
        self.assertEqual(chunks[2]['word_count'], 50)

        # Check chunk indices
        self.assertEqual(chunks[0]['chunk_index'], 0)
        self.assertEqual(chunks[1]['chunk_index'], 1)
        self.assertEqual(chunks[2]['chunk_index'], 2)

    def test_chunk_text_small_content(self):
        """Test chunking content smaller than chunk size but with enough words for validation."""
        test_words = "this content has more than ten words for validation purposes"
        chunks = self.parser.chunk_text(test_words, chunk_size=100)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['chunk_index'], 0)

    def test_chunk_text_validation_error(self):
        """Test chunking invalid content."""
        with self.assertRaises(ValueError):
            self.parser.chunk_text("short", chunk_size=100)  # Less than 10 words

        with self.assertRaises(ValueError):
            self.parser.chunk_text("", chunk_size=100)

    def test_extract_title_from_html(self):
        """Test title extraction from HTML."""
        html_content = """
        <html>
            <head>
                <title>Test Title</title>
            </head>
            <body>
                <h1>Not This Title</h1>
                <p>Some content</p>
            </body>
        </html>
        """
        title = self.parser.extract_title(html_content)
        self.assertEqual(title, "Test Title")

    def test_extract_title_from_h1_when_no_title(self):
        """Test title extraction from h1 when no title tag exists."""
        html_content = """
        <html>
            <head></head>
            <body>
                <h1>Main Title</h1>
                <p>Some content</p>
            </body>
        </html>
        """
        title = self.parser.extract_title(html_content)
        self.assertEqual(title, "Main Title")

    def test_extract_title_untitled_when_no_title_or_h1(self):
        """Test title extraction when no title or h1 exists."""
        html_content = """
        <html>
            <head></head>
            <body>
                <p>Some content</p>
            </body>
        </html>
        """
        title = self.parser.extract_title(html_content)
        self.assertEqual(title, "Untitled Content")

    def test_parse_html_content(self):
        """Test HTML content parsing."""
        html_content = """
        <html>
            <head>
                <title>Test Title</title>
                <script>console.log('test');</script>
                <style>body { color: red; }</style>
            </head>
            <body>
                <h1>Main Content</h1>
                <p>This is the main content of the page.</p>
                <p>With multiple paragraphs.</p>
            </body>
        </html>
        """
        text_content = self.parser.parse_html_content(html_content)

        # Should contain the main content
        self.assertIn("main content", text_content.lower())
        self.assertIn("multiple paragraphs", text_content.lower())

        # Should not contain script or style content
        self.assertNotIn("console.log", text_content)
        self.assertNotIn("color: red", text_content)

    def test_get_content_type_from_headers(self):
        """Test content type detection from headers."""
        url = "https://example.com/page"

        # Test HTML content type
        headers = {'content-type': 'text/html; charset=utf-8'}
        content_type = self.parser.get_content_type(url, headers)
        self.assertEqual(content_type, 'html')

        # Test JSON content type
        headers = {'content-type': 'application/json'}
        content_type = self.parser.get_content_type(url, headers)
        self.assertEqual(content_type, 'json')

        # Test text content type
        headers = {'content-type': 'text/plain'}
        content_type = self.parser.get_content_type(url, headers)
        self.assertEqual(content_type, 'text')

    def test_get_content_type_from_url_extension(self):
        """Test content type detection from URL extension."""
        # Test JSON extension
        url = "https://example.com/data.json"
        content_type = self.parser.get_content_type(url)
        self.assertEqual(content_type, 'json')

        # Test text extension
        url = "https://example.com/data.txt"
        content_type = self.parser.get_content_type(url)
        self.assertEqual(content_type, 'text')

        # Test HTML extension (default)
        url = "https://example.com/page.html"
        content_type = self.parser.get_content_type(url)
        self.assertEqual(content_type, 'html')

    def test_get_content_type_default(self):
        """Test default content type when no match is found."""
        url = "https://example.com/unknown.extension"
        content_type = self.parser.get_content_type(url)
        self.assertEqual(content_type, 'html')  # Default


if __name__ == '__main__':
    unittest.main()