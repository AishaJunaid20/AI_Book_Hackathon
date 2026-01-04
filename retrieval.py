#!/usr/bin/env python3
"""
RAG Retrieval Pipeline Validation Script

This script connects to Qdrant, loads existing vector collections,
accepts a test query, performs top-k similarity search, and validates
results using returned text, metadata, and source URLs.
"""

import os
import time
import logging
import argparse
from typing import List, Dict, Any, Optional
import cohere
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv


# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RAGRetrievalValidator:
    """Validates the RAG retrieval pipeline by connecting to Qdrant and performing similarity searches."""

    def __init__(self):
        """Initialize the validator with environment variables and clients."""
        load_dotenv()  # Load environment variables from .env file

        # Get environment variables
        self.qdrant_url = os.getenv('QDRANT_URL')
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY')
        self.cohere_api_key = os.getenv('COHERE_API_KEY')

        if not all([self.qdrant_url, self.qdrant_api_key, self.cohere_api_key]):
            raise ValueError("Missing required environment variables. Please set QDRANT_URL, QDRANT_API_KEY, and COHERE_API_KEY")

        # Initialize clients
        self.qdrant_client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            timeout=30
        )

        self.cohere_client = cohere.Client(api_key=self.cohere_api_key)

        # Default collection name
        self.collection_name = 'book_embeddings'

    def connect_and_validate_qdrant(self) -> bool:
        """Connect to Qdrant and validate that the collection exists with data."""
        try:
            # Get collection info
            collection_info = self.qdrant_client.get_collection(self.collection_name)

            print(f"SUCCESS: Connected to Qdrant successfully")
            print(f"SUCCESS: Collection '{self.collection_name}' exists")
            print(f"SUCCESS: Collection has {collection_info.points_count} points")
            print(f"SUCCESS: Vector size: {collection_info.config.params.vectors.size}")
            print(f"SUCCESS: Distance metric: {collection_info.config.params.vectors.distance}")

            # Log the connection info
            logger.info(f"Connected to Qdrant collection '{self.collection_name}' with {collection_info.points_count} points")

            return True
        except Exception as e:
            print(f"ERROR: Error connecting to Qdrant: {e}")
            logger.error(f"Error connecting to Qdrant: {e}")
            return False

    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for the query using Cohere with retry logic."""
        max_retries = 5  # Increased number of retries
        base_delay = 2  # Start with 2 seconds delay
        max_delay = 30  # Maximum delay of 30 seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"Generating embedding for query: '{query[:50]}{'...' if len(query) > 50 else ''}' (attempt {attempt + 1})")
                response = self.cohere_client.embed(
                    texts=[query],
                    model="embed-english-v3.0",  # Using the same model as the stored embeddings
                    input_type="search_query"  # Specify this is a search query
                )

                embedding = response.embeddings[0]
                print(f"SUCCESS: Generated embedding for query: '{query[:50]}{'...' if len(query) > 50 else ''}'")
                logger.info(f"Successfully generated embedding of size {len(embedding)}")
                return embedding
            except Exception as e:
                # Check if it's a rate limit error (429)
                if hasattr(e, 'status_code') and e.status_code == 429:
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        delay = min(base_delay * (2 ** attempt), max_delay)  # Exponential backoff with max delay
                        logger.warning(f"Rate limit hit (429), waiting {delay}s before retry {attempt + 2}/{max_retries}")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit hit and max retries ({max_retries}) exceeded")
                elif "429" in str(e) or "rate limit" in str(e).lower():
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        delay = min(base_delay * (2 ** attempt), max_delay)  # Exponential backoff with max delay
                        logger.warning(f"Rate limit detected in error message, waiting {delay}s before retry {attempt + 2}/{max_retries}")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit detected in error message and max retries ({max_retries}) exceeded")

                print(f"ERROR: Error generating query embedding: {e}")
                logger.error(f"Error generating query embedding: {e}")
                # Return None instead of raising to allow graceful degradation
                return None

    def search_similar_content(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar content in Qdrant."""
        max_retries = 2  # Qdrant is less likely to have rate limits, but we'll add some resilience
        base_delay = 1

        for attempt in range(max_retries):
            try:
                start_time = time.time()
                logger.info(f"Starting similarity search with k={k} (attempt {attempt + 1})")

                # Perform similarity search using query_points method (newer API)
                search_response = self.qdrant_client.query_points(
                    collection_name=self.collection_name,
                    query=query_embedding,
                    limit=k,
                    with_payload=True
                )

                search_time = time.time() - start_time

                # Extract points from the response object
                search_results = search_response.points
                print(f"SUCCESS: Found {len(search_results)} similar content chunks in {search_time:.2f}s")
                logger.info(f"Found {len(search_results)} similar content chunks in {search_time:.2f}s")

                # Format results
                formatted_results = []
                for i, result in enumerate(search_results):
                    formatted_result = {
                        'id': result.id,
                        'score': result.score,
                        'text': result.payload.get('text', ''),
                        'source_url': result.payload.get('source_url', ''),
                        'chunk_id': result.payload.get('chunk_id', ''),
                        'word_count': result.payload.get('word_count', 0),
                        'created_at': result.payload.get('created_at', '')
                    }
                    formatted_results.append(formatted_result)

                logger.info(f"Formatted {len(formatted_results)} results for return")
                return formatted_results
            except Exception as e:
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    # Check if it's a rate limit error (429) or other transient error
                    if hasattr(e, 'status_code') and e.status_code == 429 or "429" in str(e):
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limit hit during search (429), waiting {delay}s before retry {attempt + 2}/{max_retries}")
                        time.sleep(delay)
                        continue
                    elif "timeout" in str(e).lower() or "connection" in str(e).lower():
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Connection error during search, waiting {delay}s before retry {attempt + 2}/{max_retries}")
                        time.sleep(delay)
                        continue
                    else:
                        # For other errors, we don't retry
                        print(f"ERROR: Error searching for similar content: {e}")
                        logger.error(f"Error searching for similar content: {e}")
                        break
                else:
                    print(f"ERROR: Error searching for similar content after {max_retries} attempts: {e}")
                    logger.error(f"Error searching for similar content after {max_retries} attempts: {e}")
                    break

        # Return empty list instead of raising to allow graceful degradation
        return []

    def validate_results(self, results: List[Dict[str, Any]], query: str) -> bool:
        """Validate that the results are relevant and match source URLs."""
        if not results:
            print("WARNING: No results found for validation")
            logger.warning("No results found for validation")
            return False

        print(f"SUCCESS: Validating {len(results)} results:")
        logger.info(f"Validating {len(results)} results for query: '{query[:30]}{'...' if len(query) > 30 else ''}'")

        all_valid = True
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['score']:.3f} | Source: {result['source_url'][:60]}{'...' if len(result['source_url']) > 60 else ''}")
            print(f"     Content preview: {result['text'][:100]}{'...' if len(result['text']) > 100 else ''}")

            # Basic validation checks
            is_valid = True

            # Check if source URL is not empty
            if not result['source_url']:
                print(f"     WARNING: Empty source URL")
                logger.warning(f"Result {i} has empty source URL")
                is_valid = False

            # Check if text content is not empty
            if not result['text']:
                print(f"     WARNING: Empty content text")
                logger.warning(f"Result {i} has empty content text")
                is_valid = False

            # Check if content is reasonably long (not just metadata)
            if len(result['text']) < 10:
                print(f"     WARNING: Very short content ({len(result['text'])} chars)")
                logger.warning(f"Result {i} has very short content ({len(result['text'])} chars)")
                is_valid = False

            if not is_valid:
                all_valid = False
                print(f"     ERROR: Result {i} failed validation")
                logger.error(f"Result {i} failed validation")
            else:
                print(f"     SUCCESS: Result {i} passed validation")
                logger.info(f"Result {i} passed validation")

        logger.info(f"Validation complete. All valid: {all_valid}")
        return all_valid

    def run_validation(self, query: str, k: int = 5) -> bool:
        """Run the complete validation pipeline."""
        start_time = time.time()

        # Input validation
        if not query or not isinstance(query, str) or len(query.strip()) == 0:
            print("ERROR: Query cannot be empty")
            logger.error("Query cannot be empty")
            return False

        if not isinstance(k, int) or k <= 0:
            print("ERROR: k must be a positive integer")
            logger.error(f"Invalid k value: {k}")
            return False

        if k > 100:  # Set reasonable upper limit
            print("ERROR: k value too large (max 100)")
            logger.error(f"k value too large: {k}")
            return False

        print(f"INFO: Starting RAG retrieval validation for query: '{query}'")
        logger.info(f"Starting RAG retrieval validation for query: '{query}', k={k}")
        print("="*60)

        # Step 1: Connect and validate Qdrant
        if not self.connect_and_validate_qdrant():
            logger.error("Failed to connect and validate Qdrant")
            return False

        print()

        # Step 2: Generate query embedding
        query_embedding = self.generate_query_embedding(query)
        if query_embedding is None:
            print("ERROR: Failed to generate query embedding")
            logger.error("Failed to generate query embedding")
            return False

        print()

        # Step 3: Search for similar content
        results = self.search_similar_content(query_embedding, k)
        # Note: search_similar_content returns empty list on error, which is handled by validation

        print()

        # Step 4: Validate results
        validation_passed = self.validate_results(results, query)

        print()
        print("="*60)

        total_time = time.time() - start_time
        logger.info(f"RAG validation completed in {total_time:.2f}s")

        if validation_passed and results:
            print(f"SUCCESS: RAG retrieval pipeline validation PASSED")
            print(f"SUCCESS: Query '{query}' returned {len(results)} relevant results")
            print(f"SUCCESS: All results validated successfully")
            print(f"SUCCESS: Total time: {total_time:.2f}s")
            logger.info(f"RAG retrieval pipeline validation PASSED. Results: {len(results)}, Time: {total_time:.2f}s")
            return True
        else:
            print(f"ERROR: RAG retrieval pipeline validation FAILED")
            if not results:
                print(f"ERROR: No results returned for query")
            print(f"INFO: Total time: {total_time:.2f}s")
            logger.error(f"RAG retrieval pipeline validation FAILED. Time: {total_time:.2f}s")
            return False


def main():
    """Main function to run the RAG retrieval validation."""
    logger.info("Starting RAG retrieval validation")
    parser = argparse.ArgumentParser(description='RAG Retrieval Pipeline Validation')
    parser.add_argument('--query', type=str, help='Query to test the retrieval pipeline')
    parser.add_argument('--k', type=int, default=5, help='Number of top results to retrieve (default: 5)')

    args = parser.parse_args()

    # If no query provided, ask user for input
    if not args.query:
        query = input("Enter your query: ").strip()
        if not query:
            print("No query provided. Exiting.")
            logger.warning("No query provided by user")
            return
    else:
        query = args.query

    if args.k <= 0:
        print("k must be a positive integer. Using default value of 5.")
        logger.warning(f"k value {args.k} is invalid, using default value of 5")
        k = 5
    else:
        k = args.k

    logger.info(f"Running validation with query: '{query}', k: {k}")

    # Create validator instance
    validator = RAGRetrievalValidator()

    # Run validation
    success = validator.run_validation(query, k)

    if success:
        print(f"\nINFO: Validation completed successfully!")
        logger.info("Validation completed successfully")
    else:
        print(f"\nERROR: Validation failed!")
        logger.error("Validation failed")
        exit(1)


if __name__ == "__main__":
    main()