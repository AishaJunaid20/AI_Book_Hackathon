# Quickstart: RAG Retrieval Pipeline Validation

## Prerequisites

1. **Environment Variables**: Ensure the following environment variables are set:
   ```bash
   QDRANT_URL=https://fbfba02d-79f1-4209-b20c-1cf510c0be45.europe-west3-0.gcp.cloud.qdrant.io:6333
   QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.-wrOaiws6Vzj2Kk_dGOj5eNcDvIdJcTHA75IE0LI5TE
   COHERE_API_KEY=aPxj0YEi8MtBJbZixiDUoKA2E2QQ62zhzpmgh42b
   ```

2. **Dependencies**: Install required Python packages:
   ```bash
   pip install qdrant-client python-dotenv cohere requests beautifulsoup4
   ```

3. **Qdrant Collection**: Ensure the `book_embeddings` collection exists with data from previous ingestion steps.

## Setup

1. **Clone Repository**: Clone the repository with the retrieval script:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Dependencies**: Install the required packages:
   ```bash
   pip install -r requirements.txt
   # Or install individually:
   pip install qdrant-client python-dotenv cohere
   ```

3. **Set Environment Variables**: Create a `.env` file with your credentials:
   ```
   QDRANT_URL=your_qdrant_url
   QDRANT_API_KEY=your_qdrant_api_key
   COHERE_API_KEY=your_cohere_api_key
   ```

## Usage

1. **Run the Script**: Execute the retrieval script:
   ```bash
   python retrieval.py
   ```

2. **Enter Query**: When prompted, enter your text query:
   ```
   Enter your query: What is ROS 2?
   ```

3. **Set Top-K Value**: Specify how many results you want:
   ```
   Enter number of results (k): 5
   ```

4. **View Results**: The script will display:
   - Connection status to Qdrant
   - Search results with content and source URLs
   - Validation that content matches source URLs
   - Performance metrics

### Alternative Usage (Command Line Arguments)

You can also run the script with command-line arguments:

```bash
python retrieval.py --query "What is ROS 2?" --k 5
```

### Input Validation

The script includes input validation:
- Query cannot be empty
- k must be a positive integer (1-100 range)
- If Cohere API rate limits occur, the script handles them gracefully

## Example Output

```
✓ Connected to Qdrant successfully
✓ Collection 'book_embeddings' has 78 points
✓ Generated embedding for query: 'What is ROS 2?'
✓ Found 5 similar content chunks:
  1. Score: 0.892 | Source: https://ai-book-hackathon-wheat.vercel.app/docs/module1-ros2/introduction-to-ros2
     Content: 'ROS 2 (Robot Operating System 2) is a flexible framework for writing robot software...'
  2. Score: 0.876 | Source: https://ai-book-hackathon-wheat.vercel.app/docs/module1-ros2/ros2-communication-primitives
     Content: 'Communication primitives in ROS 2 include topics, services, and actions...'
✓ Validation: All results have matching source URLs and relevant content
✓ Search completed in 1.24 seconds
```

## Troubleshooting

- **Connection Error**: Verify QDRANT_URL and QDRANT_API_KEY are correct
- **API Key Error**: Check that COHERE_API_KEY is valid and has sufficient quota
- **No Results**: Ensure the `book_embeddings` collection has data
- **Rate Limit**: If getting Cohere rate limit errors, wait before making another query