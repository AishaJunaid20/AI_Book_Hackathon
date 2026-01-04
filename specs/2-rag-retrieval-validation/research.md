# Research: RAG Retrieval Pipeline Validation

## Objective
Research and document the approach for creating a single Python script that connects to Qdrant, loads existing vector collections, accepts test queries, performs top-k similarity search, and validates results using returned text, metadata, and source URLs.

## Decision: Qdrant Connection and Query Approach
**Rationale**: Use the existing Qdrant client library with credentials from environment variables to connect to the existing collection "book_embeddings" created in previous work.

**Alternatives considered**:
- Using REST API directly: More complex and error-prone than using the official client
- Creating new collection: Not needed since we're validating existing embeddings

## Decision: Embedding Generation for Queries
**Rationale**: Since we're validating existing embeddings, we'll use Cohere API to generate embeddings for test queries to match the format of existing embeddings (1024-dimensional vectors with Cosine distance).

**Alternatives considered**:
- Using different embedding model: Would not match existing embeddings format
- Random embeddings: Would not provide meaningful similarity search

## Decision: Validation Approach
**Rationale**: Validate results by checking that returned content chunks match their source URLs, and that the content is semantically related to the query.

**Alternatives considered**:
- Only checking source URLs: Would not validate content relevance
- Only checking content relevance: Would not validate data integrity

## Technical Implementation Details

### Required Dependencies
- qdrant-client: For connecting to Qdrant and performing searches
- python-dotenv: For loading environment variables
- cohere: For generating embeddings for queries
- requests, beautifulsoup4: For content validation (already available from previous work)

### Qdrant Collection Information
From previous work, we know:
- Collection name: `book_embeddings`
- Vector size: 1024 dimensions
- Distance metric: Cosine
- Existing content: Book content from https://ai-book-hackathon-wheat.vercel.app/

### Script Workflow
1. Load environment variables (QDRANT_URL, QDRANT_API_KEY, COHERE_API_KEY)
2. Connect to Qdrant client
3. Accept user query input
4. Generate embedding for query using Cohere
5. Perform similarity search in Qdrant
6. Validate results (content matches source URLs, relevance to query)
7. Display results with metadata