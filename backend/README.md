# Embeddings Generation Service

This service fetches content from URLs, generates embeddings using Cohere, and stores them in Qdrant for retrieval.

## Overview

The Embeddings Generation Service processes book content by:
1. Fetching content from a specified URL
2. Parsing and chunking the content into manageable pieces
3. Generating embeddings using Cohere's embedding model
4. Storing the embeddings in Qdrant vector database for retrieval

## Prerequisites

- Python 3.11+
- Cohere API key
- Qdrant Cloud account and API key

## Setup

### Local Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd embeddings-service
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Copy the `.env` file and set your API keys:
     ```bash
     cp .env .env.local
     ```
   - Edit `.env.local` and add your Cohere and Qdrant API keys

5. Configure application settings in `config.yaml` if needed

### Cloud Setup

1. Deploy to your preferred cloud platform (AWS, GCP, Azure, or Vercel)
2. Set environment variables in your cloud platform:
   - `COHERE_API_KEY`: Your Cohere API key
   - `QDRANT_URL`: Your Qdrant cluster URL
   - `QDRANT_API_KEY`: Your Qdrant API key
   - `QDRANT_COLLECTION_NAME`: Name of the Qdrant collection (optional, defaults to 'book_embeddings')
3. Ensure your cloud environment can access the URLs you want to process

## Usage

### Command Line

Run the main script to process content:
```bash
cd backend
python src/main.py --url "https://example.com/book-content"
```

Optional arguments:
- `--config`: Path to config file (default: config.yaml)
- `--debug`: Enable debug logging

### Example Usage

```bash
# Process a book URL
python src/main.py --url "https://example.com/book"

# Process with debug output
python src/main.py --url "https://example.com/book" --debug
```

## Architecture

The service is organized into:
- `src/models/` - Data models for content, chunks, embeddings, and jobs
- `src/services/` - Business logic for content parsing, embedding generation, and Qdrant operations
- `src/utils/` - Configuration and utility functions

### Key Components

- `content_parser.py` - Fetches and parses content from URLs
- `embedding_generator.py` - Generates embeddings using Cohere API
- `qdrant_service.py` - Stores and retrieves embeddings from Qdrant
- `main.py` - Main workflow orchestrator

## Configuration

### Environment Variables

The application uses the following environment variables:

- `COHERE_API_KEY`: Your Cohere API key for generating embeddings
- `QDRANT_URL`: Your Qdrant cluster URL (e.g., https://your-cluster.qdrant.tech:6333)
- `QDRANT_API_KEY`: Your Qdrant API key for authentication
- `QDRANT_COLLECTION_NAME`: Name of the Qdrant collection to use (optional, defaults to 'book_embeddings')

### Configuration File

The application uses `config.yaml` for additional configuration options:

```yaml
cohere:
  api_key: ${COHERE_API_KEY}  # Reference to environment variable
  model: "embed-english-v3.0"  # Cohere embedding model to use
  embedding_size: 1024  # Size of the embedding vectors

qdrant:
  url: ${QDRANT_URL}  # Reference to environment variable
  api_key: ${QDRANT_API_KEY}  # Reference to environment variable
  collection_name: ${QDRANT_COLLECTION_NAME:-book_embeddings}  # Default to 'book_embeddings'
  vector_size: 1024  # Size of vectors in Qdrant
  distance: "Cosine"  # Distance metric for similarity search

processing:
  chunk_size: 1000  # Number of words per content chunk
  max_concurrent_requests: 5  # Maximum concurrent requests to Cohere
  retry_attempts: 3  # Number of retry attempts for failed requests
  timeout: 30  # Request timeout in seconds

api:
  host: "0.0.0.0"  # Host to bind the API server to
  port: 8000  # Port for the API server
  rate_limit: 100  # Requests per minute rate limit
```

## API Documentation

The service provides the following API endpoints:

### POST /process-url
Process content from a URL, generate embeddings, and store in Qdrant.

**Request:**
```json
{
  "url": "https://example.com/book-content",
  "collection_name": "book_embeddings",
  "chunk_size": 1000,
  "model": "embed-english-v3.0"
}
```

**Response (202):**
```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "message": "Content processing started",
  "total_chunks": 45,
  "estimated_time_seconds": 120
}
```

### GET /job-status/{job_id}
Get the status of a content processing job.

**Response (200):**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "total_chunks": 45,
  "processed_chunks": 45,
  "created_at": "2026-01-01T10:00:00Z",
  "completed_at": "2026-01-01T10:02:30Z",
  "embeddings_count": 45,
  "collection_name": "book_embeddings"
}
```

### POST /search
Search for similar content using embeddings.

**Request:**
```json
{
  "query": "text to search for similarity",
  "collection_name": "book_embeddings",
  "limit": 5
}
```

**Response (200):**
```json
{
  "results": [
    {
      "id": "embedding-uuid",
      "score": 0.85,
      "payload": {
        "text": "text snippet from the original content",
        "chunk_id": "chunk-uuid",
        "book_content_id": "book-uuid"
      }
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### API Key Issues
- **Error**: "Invalid API key" or "Authentication failed"
- **Solution**: Verify that your Cohere and Qdrant API keys are correctly set in your environment variables

#### Network Issues
- **Error**: "Connection timeout" or "Failed to fetch URL"
- **Solution**: Check that the URL is accessible and that your network allows outbound connections

#### Rate Limiting
- **Error**: "Rate limit exceeded" from Cohere
- **Solution**: The application implements retry logic, but you may need to adjust the processing rate based on your Cohere plan

#### Qdrant Connection Issues
- **Error**: "Failed to connect to Qdrant"
- **Solution**: Verify that your QDRANT_URL and QDRANT_API_KEY are correct and that your network allows connections to Qdrant

#### Large Content Processing
- **Issue**: Processing very large documents may take longer
- **Solution**: The application chunks content into 1000-word segments by default, which can be adjusted in config.yaml

### Checking Service Status

To verify that all services are working correctly:

1. Check that the application can connect to Cohere:
   ```bash
   python -c "import cohere; client = cohere.Client('your-api-key'); print(client.embed(['test'], model='embed-english-v3.0'))"
   ```

2. Check that the application can connect to Qdrant:
   ```bash
   python -c "from qdrant_client import QdrantClient; client = QdrantClient(url='your-url', api_key='your-key'); print(client.get_collections())"
   ```

### GET /collections
List available Qdrant collections.

**Response (200):**
```json
{
  "collections": [
    {
      "name": "book_embeddings",
      "vectors_count": 1250,
      "vector_size": 1024,
      "distance": "Cosine"
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### API Key Issues
- **Error**: "Invalid API key" or "Authentication failed"
- **Solution**: Verify that your Cohere and Qdrant API keys are correctly set in your environment variables

#### Network Issues
- **Error**: "Connection timeout" or "Failed to fetch URL"
- **Solution**: Check that the URL is accessible and that your network allows outbound connections

#### Rate Limiting
- **Error**: "Rate limit exceeded" from Cohere
- **Solution**: The application implements retry logic, but you may need to adjust the processing rate based on your Cohere plan

#### Qdrant Connection Issues
- **Error**: "Failed to connect to Qdrant"
- **Solution**: Verify that your QDRANT_URL and QDRANT_API_KEY are correct and that your network allows connections to Qdrant

#### Large Content Processing
- **Issue**: Processing very large documents may take longer
- **Solution**: The application chunks content into 1000-word segments by default, which can be adjusted in config.yaml

### Checking Service Status

To verify that all services are working correctly:

1. Check that the application can connect to Cohere:
   ```bash
   python -c "import cohere; client = cohere.Client('your-api-key'); print(client.embed(['test'], model='embed-english-v3.0'))"
   ```

2. Check that the application can connect to Qdrant:
   ```bash
   python -c "from qdrant_client import QdrantClient; client = QdrantClient(url='your-url', api_key='your-key'); print(client.get_collections())"
   ```