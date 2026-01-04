# Data Model: RAG Retrieval Pipeline Validation

## Entities

### Retrieval Query
- **Description**: Text input from user that serves as basis for semantic search
- **Fields**:
  - query_text: string (the original query text)
  - query_embedding: list[float] (1024-dimensional vector representation)
  - timestamp: datetime (when query was made)

### Content Chunk
- **Description**: Text segment retrieved from vector database that matches the query
- **Fields**:
  - id: string (unique identifier from Qdrant)
  - text: string (the actual content text)
  - vector: list[float] (1024-dimensional embedding vector)
  - score: float (similarity score from search)

### Source Metadata
- **Description**: Information about where the content originated
- **Fields**:
  - source_url: string (original URL where content came from)
  - chunk_id: string (ID of the original chunk)
  - word_count: int (number of words in the chunk)
  - created_at: string (timestamp when chunk was created)

### Search Results
- **Description**: Collection of content chunks returned for a query
- **Fields**:
  - query: Retrieval Query (the original query)
  - results: list[Content Chunk] (top-k matching chunks)
  - total_points: int (total points in the collection)
  - search_time: float (time taken to perform search in seconds)

## Validation Rules

### Content Validation
- Content chunks must contain meaningful text (not empty or just metadata)
- Source URLs in metadata must match the actual source of the content
- Text content must be semantically related to the original query

### Metadata Validation
- All required metadata fields (source_url, chunk_id, word_count) must be present
- Source URLs must be valid and accessible
- Created timestamp should be within reasonable range

### Search Validation
- Top-k results should be returned (or fewer if less exist in collection)
- Results should be ordered by relevance (highest score first)
- Search should complete within acceptable time limits (5 seconds)