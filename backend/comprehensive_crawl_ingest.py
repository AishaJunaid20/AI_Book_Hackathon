#!/usr/bin/env python3
"""
Comprehensive script to crawl and ingest ALL content from the deployed site into Qdrant
"""

import os
import requests
from bs4 import BeautifulSoup
import random
from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.http import models
from urllib.parse import urljoin, urlparse
import time
import logging


# Set up logging to avoid the Unicode display issues
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def is_valid_url(url, base_domain):
    """Check if URL is valid and belongs to the same domain."""
    parsed = urlparse(url)
    base_parsed = urlparse(base_domain)
    return parsed.netloc == base_parsed.netloc


def extract_internal_links(html_content, base_url):
    """Extract all internal links from the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()

    for link in soup.find_all(['a', 'link'], href=True):
        href = link['href']
        full_url = urljoin(base_url, href)

        # Only include internal links that don't end with non-HTML files
        if is_valid_url(full_url, base_url) and not full_url.endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.exe', '.css', '.js', '.ico', '.svg')):
            # Normalize the URL by removing fragments and query parameters
            normalized_url = full_url.split('#')[0].split('?')[0]
            if normalized_url != base_url:  # Don't include the base URL itself multiple times
                links.add(normalized_url)

    return links


def fetch_content_from_url(url: str) -> str:
    """Fetch and extract text content from the given URL."""
    logger.info(f"Fetching content from: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return ""


def extract_text_from_html(html: str) -> str:
    """Extract clean text from HTML content."""
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script, style, nav, footer, and other non-content elements
    for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        element.decompose()

    # Get text content
    text = soup.get_text()

    # Clean up text - remove extra whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)

    return text


def chunk_text(text: str, chunk_size: int = 500) -> list:
    """Split text into chunks of specified size."""
    if not text:
        return []

    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():  # Only add non-empty chunks
            chunks.append({
                'id': str(uuid4()),
                'text': chunk,
                'word_count': len(chunk.split()),
                'source_url': None  # Will be set when processing each URL
            })

    logger.info(f"Text split into {len(chunks)} chunks")
    return chunks


def create_mock_embedding(size: int = 1024) -> list:
    """Create a random embedding vector for testing purposes."""
    return [random.random() * 2 - 1 for _ in range(size)]  # Values between -1 and 1


def store_in_qdrant_batch(chunks: list, collection_name: str, batch_size: int = 50):
    """Store the chunks in Qdrant with mock embeddings in batches to avoid memory issues."""
    # Initialize Qdrant client
    client = QdrantClient(
        url=os.environ['QDRANT_URL'],
        api_key=os.environ['QDRANT_API_KEY'],
        timeout=30
    )

    total_chunks = len(chunks)
    stored_count = 0

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i + batch_size]

        # Prepare points for batch upload
        points = []
        for chunk in batch:
            embedding = create_mock_embedding()

            payload = {
                'text': chunk['text'][:2000],  # Limit text length in payload to avoid size limits
                'source_url': chunk.get('source_url', ''),
                'chunk_id': chunk['id'],
                'word_count': chunk['word_count'],
                'created_at': str(__import__('datetime').datetime.now())
            }

            points.append(models.PointStruct(
                id=chunk['id'],
                vector=embedding,
                payload=payload
            ))

        # Upload points to Qdrant
        if points:
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            stored_count += len(points)
            logger.info(f"Stored batch: {len(points)} chunks ({stored_count}/{total_chunks} total)")

    logger.info(f"Successfully stored {stored_count} chunks in Qdrant collection '{collection_name}'")


def crawl_entire_site(base_url: str, max_pages: int = 100):
    """Crawl the entire site and ingest content from all discovered pages."""
    visited_urls = set()
    urls_to_visit = [base_url]
    all_chunks = []

    page_count = 0
    while urls_to_visit and page_count < max_pages:
        current_url = urls_to_visit.pop(0)

        if current_url in visited_urls:
            continue

        visited_urls.add(current_url)
        page_count += 1
        logger.info(f"Processing URL ({page_count}/{max_pages}): {current_url}")

        # Fetch HTML content
        html_content = fetch_content_from_url(current_url)
        if not html_content:
            continue

        # Extract text content
        text_content = extract_text_from_html(html_content)
        if not text_content.strip():
            logger.info("No text content found, skipping...")
            continue

        # Create chunks from the content
        chunks = chunk_text(text_content, chunk_size=500)
        for chunk in chunks:
            chunk['source_url'] = current_url

        all_chunks.extend(chunks)
        logger.info(f"Extracted {len(chunks)} chunks from {current_url}")

        # Extract internal links to continue crawling
        internal_links = extract_internal_links(html_content, base_url)
        for link in internal_links:
            if link not in visited_urls and link not in urls_to_visit:
                urls_to_visit.append(link)

        # Be respectful to the server
        time.sleep(0.2)

    return all_chunks, visited_urls


def main():
    # Set environment variables
    os.environ['QDRANT_URL'] = 'https://fbfba02d-79f1-4209-b20c-1cf510c0be45.europe-west3-0.gcp.cloud.qdrant.io:6333'
    os.environ['QDRANT_API_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.-wrOaiws6Vzj2Kk_dGOj5eNcDvIdJcTHA75IE0LI5TE'
    collection_name = 'book_embeddings'

    base_url = "https://ai-book-hackathon-wheat.vercel.app/"

    try:
        logger.info("Starting comprehensive site crawl and ingestion...")

        # Crawl the entire site and collect all content
        all_chunks, visited_urls = crawl_entire_site(base_url, max_pages=100)

        logger.info(f"\nCrawling completed!")
        logger.info(f"Visited {len(visited_urls)} unique URLs")
        logger.info(f"Collected {len(all_chunks)} total content chunks")

        # Store all content in Qdrant
        if all_chunks:
            logger.info("Starting storage process...")
            store_in_qdrant_batch(all_chunks, collection_name)
        else:
            logger.warning("No content was collected to store.")

        # Verify the collection now has more points
        client = QdrantClient(
            url=os.environ['QDRANT_URL'],
            api_key=os.environ['QDRANT_API_KEY'],
            timeout=10
        )

        collection_info = client.get_collection(collection_name)
        logger.info(f"\nCollection '{collection_name}' now has {collection_info.points_count} points")

        # Show sample points
        logger.info("\nSample points stored:")
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=10
        )

        points, _ = scroll_result
        for i, point in enumerate(points):
            payload = point.payload
            logger.info(f"Point {i+1}:")
            logger.info(f"  ID: {point.id}")
            logger.info(f"  Source URL: {payload.get('source_url', 'N/A')[0:80]}...")
            logger.info(f"  Text preview: {payload.get('text', '')[0:100]}...")
            logger.info(f"  Word count: {payload.get('word_count', 'N/A')}")

        logger.info(f"\nCrawling Summary:")
        logger.info(f"- URLs crawled: {len(visited_urls)}")
        logger.info(f"- Content chunks: {len(all_chunks)}")
        logger.info(f"- Points in Qdrant: {collection_info.points_count}")

    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()