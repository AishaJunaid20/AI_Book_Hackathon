#!/usr/bin/env python3
"""
Script to ingest content from the deployed URL into Qdrant with mock embeddings
to bypass Cohere API rate limits.
"""

import os
import requests
from bs4 import BeautifulSoup
import random
from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.http import models


def fetch_content_from_url(url: str) -> str:
    """Fetch and extract text content from the given URL."""
    print(f"Fetching content from: {url}")
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text content
    text = soup.get_text()

    # Clean up text
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)

    print(f"Successfully fetched content: {len(text)} characters")
    return text


def chunk_text(text: str, chunk_size: int = 500) -> list:
    """Split text into chunks of specified size."""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():  # Only add non-empty chunks
            chunks.append({
                'id': str(uuid4()),
                'text': chunk,
                'word_count': len(chunk.split())
            })

    print(f"Text split into {len(chunks)} chunks")
    return chunks


def create_mock_embedding(size: int = 1024) -> list:
    """Create a random embedding vector for testing purposes."""
    return [random.random() * 2 - 1 for _ in range(size)]  # Values between -1 and 1


def store_in_qdrant(chunks: list, collection_name: str, url: str):
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
            'source_url': url,
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


def main():
    # Set environment variables (these should be available from the .env file)
    os.environ['QDRANT_URL'] = 'https://fbfba02d-79f1-4209-b20c-1cf510c0be45.europe-west3-0.gcp.cloud.qdrant.io:6333'
    os.environ['QDRANT_API_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.-wrOaiws6Vzj2Kk_dGOj5eNcDvIdJcTHA75IE0LI5TE'
    collection_name = 'book_embeddings'

    url = "https://ai-book-hackathon-wheat.vercel.app/"

    try:
        # Fetch content from URL
        content = fetch_content_from_url(url)

        # Chunk the content
        chunks = chunk_text(content, chunk_size=200)  # Smaller chunks for better granularity

        # Store in Qdrant
        store_in_qdrant(chunks, collection_name, url)

        # Verify the collection now has more points
        client = QdrantClient(
            url=os.environ['QDRANT_URL'],
            api_key=os.environ['QDRANT_API_KEY'],
            timeout=10
        )

        collection_info = client.get_collection(collection_name)
        print(f"Collection '{collection_name}' now has {collection_info.points_count} points")

    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise


if __name__ == "__main__":
    main()