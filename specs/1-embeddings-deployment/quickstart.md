# Quickstart Guide: Website Deployment & Embeddings

## Prerequisites

- Python 3.11 or higher
- Git
- Cohere API key
- Qdrant Cloud account and API key
- Access to book content URL

## Setup

### 1. Clone the repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Set up Python environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the backend directory:
```env
COHERE_API_KEY=your_cohere_api_key_here
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_URL=your_qdrant_cluster_url
QDRANT_COLLECTION_NAME=book_embeddings
```

## Running the Embedding Process

### 1. Prepare configuration
Edit `backend/config.yaml` to specify:
- Source URL for book content
- Chunk size parameters
- Qdrant collection settings

### 2. Run the main script
```bash
cd backend
python src/main.py --url "https://your-book-content-url.com" --collection "book_embeddings"
```

### 3. Monitor the process
The script will:
- Fetch content from the specified URL
- Parse and chunk the content
- Generate embeddings using Cohere
- Store embeddings in Qdrant
- Provide progress updates

## Verification

### Check Qdrant collection
After completion, verify embeddings are stored:
```python
import qdrant_client
from qdrant_client.http import models

client = qdrant_client.QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

collection_info = client.get_collection("book_embeddings")
print(f"Points in collection: {collection_info.points_count}")
```

### Test retrieval
```bash
# Example retrieval command
python src/main.py --test-retrieval --query "your search query here"
```

## Local Development

### Running tests
```bash
pytest tests/
```

### Running with debug output
```bash
python src/main.py --url "https://example.com" --debug
```

## Cloud Deployment

### Docker build
```bash
docker build -t embeddings-processor .
docker run -e COHERE_API_KEY=... -e QDRANT_API_KEY=... embeddings-processor
```

### Environment setup for cloud
When deploying to cloud environments, ensure:
- Secure handling of API keys
- Proper network access to source URLs
- Adequate memory for processing large content
- Monitoring and logging for production use