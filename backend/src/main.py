"""Main script for the embeddings generation service."""

import argparse
import logging
import sys
import os
from typing import List, Dict, Any
import uuid

# Add the backend directory to the Python path to enable proper imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.services.content_parser import ContentParser
from src.services.embedding_generator import EmbeddingGenerator
from src.services.qdrant_service import QdrantService
from src.utils.config import Config
from src.models.embedding import ProcessingJob, BookContent, ContentChunk, Embedding


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def validate_url(url: str) -> bool:
    """Validate URL format."""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and url_pattern.match(url) is not None


def process_url_to_embeddings(url: str, config: Config, debug: bool = False):
    """Main workflow: get URL → chunk content → generate embeddings → store in Qdrant."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate inputs
    if not url or not isinstance(url, str):
        logging.error("Invalid URL provided")
        return False

    if not validate_url(url):
        logging.error(f"Invalid URL format: {url}")
        return False

    logging.info(f"Starting processing for URL: {url}")

    # Initialize services
    content_parser = ContentParser(chunk_size=config.chunk_size)
    embedding_generator = EmbeddingGenerator(config)
    qdrant_service = QdrantService(config)

    # Create a processing job
    job_id = str(uuid.uuid4())
    logging.info(f"Created processing job with ID: {job_id}")

    # Step 1: Fetch and parse content
    logging.info("Step 1: Fetching and parsing content...")
    content_data = content_parser.process_and_chunk_url(url)

    if not content_data:
        logging.error(f"Failed to fetch content from {url}")
        return False

    logging.info(f"Successfully fetched content: {content_data['title']}")
    logging.info(f"Content length: {content_data['word_count']} words")
    logging.info(f"Content split into {content_data['total_chunks']} chunks")

    # Step 2: Generate embeddings for all chunks
    logging.info("Step 2: Generating embeddings...")
    chunks = content_data['chunks']
    texts = [chunk['text'] for chunk in chunks]

    embeddings = embedding_generator.batch_generate_embeddings(texts)

    if not embeddings:
        logging.error("Failed to generate embeddings")
        return False

    logging.info(f"Successfully generated {len(embeddings)} embeddings")

    # Step 3: Store embeddings in Qdrant
    logging.info("Step 3: Storing embeddings in Qdrant...")

    # Prepare metadata for each chunk
    metadata_list = []
    for i, chunk in enumerate(chunks):
        metadata = {
            'chunk_index': chunk['chunk_index'],
            'word_count': chunk['word_count'],
            'source_url': url,
            'source_title': content_data['title'],
            'chunk_id': chunk['id']
        }
        metadata_list.append(metadata)

    try:
        record_ids = qdrant_service.store_embeddings_batch(
            texts=texts,
            embeddings=embeddings,
            metadata_list=metadata_list
        )
        logging.info(f"Successfully stored {len(record_ids)} embeddings in Qdrant")
    except Exception as e:
        logging.error(f"Failed to store embeddings in Qdrant: {e}")
        return False

    logging.info(f"Processing completed successfully. Stored {len(record_ids)} embeddings.")
    logging.info(f"Job ID: {job_id}")

    return True


def main():
    """Main function with command-line interface."""
    setup_logging()

    parser = argparse.ArgumentParser(description="Embeddings Generation Service")
    parser.add_argument("--url", required=True, help="URL to process for embeddings")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Load configuration
    try:
        config = Config(args.config)
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Process the URL
    success = process_url_to_embeddings(args.url, config, args.debug)

    if success:
        logging.info("Embedding generation completed successfully")
        sys.exit(0)
    else:
        logging.error("Embedding generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()