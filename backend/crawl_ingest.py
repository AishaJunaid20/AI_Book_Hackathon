#!/usr/bin/env python3
"""
Script to crawl the deployed site and ingest all content into Qdrant
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


def is_valid_url(url, base_domain):
    """Check if URL is valid and belongs to the same domain."""
    parsed = urlparse(url)
    base_parsed = urlparse(base_domain)
    return parsed.netloc == base_parsed.netloc


def extract_internal_links(html_content, base_url):
    """Extract all internal links from the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()

    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)

        if is_valid_url(full_url, base_url) and not full_url.endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.exe')):
            # Normalize the URL by removing fragments
            normalized_url = full_url.split('#')[0]
            links.add(normalized_url)

    return links


def fetch_content_from_url(url: str) -> str:
    """Fetch and extract text content from the given URL."""
    print(f"Fetching content from: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""


def extract_text_from_html(html: str) -> str:
    """Extract clean text from HTML content."""
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text content
    text = soup.get_text()

    # Clean up text
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

    print(f"Text split into {len(chunks)} chunks")
    return chunks


def create_mock_embedding(size: int = 1024) -> list:
    """Create a random embedding vector for testing purposes."""
    return [random.random() * 2 - 1 for _ in range(size)]  # Values between -1 and 1


def store_in_qdrant(chunks: list, collection_name: str):
    """Store the chunks in Qdrant with mock embeddings."""
    # Initialize Qdrant client
    client = QdrantClient(
        url=os.environ['QDRANT_URL'],
        api_key=os.environ['QDRANT_API_KEY'],
        timeout=10
    )

    # Prepare points for batch upload
    points = []
    for chunk in chunks:
        embedding = create_mock_embedding()

        payload = {
            'text': chunk['text'][:1000],  # Limit text length in payload
            'source_url': chunk.get('source_url', ''),
            'chunk_id': chunk['id'],
            'word_count': chunk['word_count'],
            'created_at': str(__import__('datetime').datetime.utcnow())
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
        print(f"Successfully stored {len(points)} chunks in Qdrant collection '{collection_name}'")
    else:
        print("No points to store")


def crawl_and_ingest(base_url: str, max_pages: int = 10):
    """Crawl the site and ingest content from all discovered pages."""
    visited_urls = set()
    urls_to_visit = [base_url]
    all_chunks = []

    while urls_to_visit and len(visited_urls) < max_pages:
        current_url = urls_to_visit.pop(0)

        if current_url in visited_urls:
            continue

        visited_urls.add(current_url)
        print(f"\nProcessing URL ({len(visited_urls)}/{max_pages}): {current_url}")

        # Fetch HTML content
        html_content = fetch_content_from_url(current_url)
        if not html_content:
            continue

        # Extract text content
        text_content = extract_text_from_html(html_content)
        if not text_content.strip():
            print("No text content found, skipping...")
            continue

        # Create chunks from the content
        chunks = chunk_text(text_content, chunk_size=500)
        for chunk in chunks:
            chunk['source_url'] = current_url

        all_chunks.extend(chunks)
        print(f"Extracted {len(chunks)} chunks from {current_url}")

        # Extract internal links to continue crawling
        internal_links = extract_internal_links(html_content, base_url)
        for link in internal_links:
            if link not in visited_urls and link not in urls_to_visit:
                urls_to_visit.append(link)

        # Be respectful to the server
        time.sleep(0.5)

    return all_chunks


def main():
    # Set environment variables
    os.environ['QDRANT_URL'] = 'https://fbfba02d-79f1-4209-b20c-1cf510c0be45.europe-west3-0.gcp.cloud.qdrant.io:6333'
    os.environ['QDRANT_API_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.-wrOaiws6Vzj2Kk_dGOj5eNcDvIdJcTHA75IE0LI5TE'
    collection_name = 'book_embeddings'

    base_url = "https://ai-book-hackathon-wheat.vercel.app/"

    try:
        print("Starting site crawl and ingestion...")

        # Crawl the site and collect all content
        all_chunks = crawl_and_ingest(base_url, max_pages=10)

        print(f"\nCollected {len(all_chunks)} total chunks from {10} pages maximum")

        # Store all content in Qdrant
        if all_chunks:
            store_in_qdrant(all_chunks, collection_name)

        # Verify the collection now has more points
        client = QdrantClient(
            url=os.environ['QDRANT_URL'],
            api_key=os.environ['QDRANT_API_KEY'],
            timeout=10
        )

        collection_info = client.get_collection(collection_name)
        print(f"\nCollection '{collection_name}' now has {collection_info.points_count} points")

        # Show sample points
        print("\nSample points stored:")
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=5
        )

        points, _ = scroll_result
        for i, point in enumerate(points):
            payload = point.payload
            print(f"Point {i+1}:")
            print(f"  ID: {point.id}")
            print(f"  Source URL: {payload.get('source_url', 'N/A')}")
            print(f"  Text preview: {payload.get('text', '')[0:100]}...")
            print(f"  Word count: {payload.get('word_count', 'N/A')}")

    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise


if __name__ == "__main__":
    main()