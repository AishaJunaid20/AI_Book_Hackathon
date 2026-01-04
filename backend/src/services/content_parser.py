"""Service for fetching and parsing content from URLs."""

import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from urllib.parse import urljoin, urlparse
import re
import logging


class ContentParser:
    """Service to fetch and parse content from URLs."""

    def __init__(self, timeout: int = 30, chunk_size: int = 1000):
        """Initialize the content parser with a timeout and chunk size."""
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.session = requests.Session()
        # Set a user agent to avoid being blocked by some websites
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_content(self, url: str) -> Optional[str]:
        """Fetch content from the given URL."""
        try:
            logging.info(f"Fetching content from URL: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()  # Raise an exception for bad status codes
            logging.info(f"Successfully fetched {len(response.text)} characters from {url}")
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching content from {url}: {e}")
            return None

    def parse_html_content(self, html_content: str) -> str:
        """Parse HTML content and extract text."""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Clean up the text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def extract_title(self, html_content: str) -> str:
        """Extract title from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        # If no title tag, try h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()[:100]  # Limit length

        return "Untitled Content"

    def get_content_type(self, url: str, response_headers: dict = None) -> str:
        """Determine content type based on URL and headers."""
        if response_headers and 'content-type' in response_headers:
            content_type = response_headers['content-type'].lower()
            if 'text/html' in content_type:
                return 'html'
            elif 'application/json' in content_type:
                return 'json'
            elif 'text/plain' in content_type:
                return 'text'

        # Fallback to URL extension
        parsed_url = urlparse(url)
        if parsed_url.path.endswith('.json'):
            return 'json'
        elif parsed_url.path.endswith('.txt'):
            return 'text'
        else:
            return 'html'  # Default to HTML

    def validate_content(self, content: str) -> bool:
        """Validate content meets basic requirements."""
        if not content or len(content.strip()) == 0:
            return False

        # Check if content has at least some meaningful text
        words = content.split()
        if len(words) < 10:  # At least 10 words
            return False

        return True

    def sanitize_content(self, content: str) -> str:
        """Sanitize content by removing problematic characters and patterns."""
        if not content:
            return ""

        # Remove null bytes and other problematic characters
        content = content.replace('\x00', '')

        # Normalize whitespace
        import re
        content = re.sub(r'\s+', ' ', content)

        # Remove excessive newlines (keep at most 2)
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content.strip()

    def chunk_text(self, text: str, chunk_size: int = None) -> List[Dict[str, any]]:
        """Chunk text into smaller pieces based on word count."""
        if chunk_size is None:
            chunk_size = self.chunk_size

        logging.info(f"Chunking text of length {len(text)} with chunk size {chunk_size}")

        # Sanitize the text before chunking
        text = self.sanitize_content(text)

        # Validate the text
        if not self.validate_content(text):
            raise ValueError("Content does not meet validation requirements")

        words = text.split()
        chunks = []
        chunk_index = 0

        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)

            chunk_data = {
                'id': f"chunk_{chunk_index}",
                'text': chunk_text,
                'chunk_index': chunk_index,
                'word_count': len(chunk_words),
                'metadata': {}
            }

            chunks.append(chunk_data)
            chunk_index += 1

        logging.info(f"Created {len(chunks)} chunks from text")
        return chunks

    def process_url(self, url: str) -> Optional[dict]:
        """Process a URL and return structured content data."""
        try:
            html_content = self.fetch_content(url)
            if not html_content:
                logging.error(f"Failed to fetch content from URL: {url}")
                return None

            content_type = self.get_content_type(url, {'content-type': 'text/html'})
            text_content = self.parse_html_content(html_content)
            title = self.extract_title(html_content)

            return {
                'url': url,
                'title': title,
                'content': text_content,
                'content_type': content_type,
                'word_count': len(text_content.split())
            }
        except Exception as e:
            logging.error(f"Error processing URL {url}: {e}")
            return None

    def process_and_chunk_url(self, url: str) -> Optional[dict]:
        """Process a URL and return structured content data with chunks."""
        content_data = self.process_url(url)
        if not content_data:
            return None

        # Create chunks from the content
        chunks = self.chunk_text(content_data['content'])

        return {
            **content_data,
            'chunks': chunks,
            'total_chunks': len(chunks)
        }


def count_words(text: str) -> int:
    """Count the number of words in a text string."""
    # Use regex to split on any whitespace and remove empty strings
    words = [word for word in re.split(r'\s+', text.strip()) if word]
    return len(words)