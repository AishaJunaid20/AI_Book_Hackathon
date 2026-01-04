# Tasks: Website Deployment & Embeddings

## Feature Overview
Deploy book website, parse content, and generate embeddings using Cohere. Store embeddings in Qdrant Cloud Free Tier with unique IDs for retrieval. Create a backend folder with a single main.py containing all functionality: get URL → chunk content → generate embeddings → store in Qdrant → run main function. Verify embeddings retrieval and document deployment & embedding pipeline.

**Feature Branch**: `1-embeddings-deployment`

## Dependencies
- User Story 2 (Generate text embeddings) depends on User Story 1 (Deploy website content) for content access
- User Story 3 (Store embeddings) depends on User Story 2 (Generate embeddings) for embedding data
- User Story 4 (Documentation) can be done in parallel but should be updated as other stories progress

## Parallel Execution Examples
- Setup tasks (requirements, config files) can run in parallel with documentation creation
- Service implementations (content_parser, embedding_generator, qdrant_service) can be developed in parallel
- Unit tests can be written in parallel with service implementations

## Implementation Strategy
- MVP: Basic functionality to fetch content from a URL, generate embeddings using Cohere, and store them in Qdrant
- Incremental delivery: Start with US1 and US2, then add US3, finally US4
- Focus on core functionality first, add error handling and edge cases later

## Phase 1: Setup Tasks
- [X] T001 Create backend directory structure as specified in plan.md
- [X] T002 Create requirements.txt with dependencies: cohere, qdrant-client, requests, beautifulsoup4, PyYAML, python-dotenv
- [X] T003 Create initial config.yaml file with configuration structure from plan.md
- [X] T004 Create .env file template with API key placeholders
- [X] T005 Create README.md with basic project description

## Phase 2: Foundational Tasks
- [X] T006 [P] Create models/ directory and embedding.py with BookContent, ContentChunk, Embedding, QdrantRecord, and ProcessingJob classes
- [X] T007 [P] Create utils/ directory and config.py for configuration management
- [X] T008 [P] Create services/ directory and __init__.py files for all modules

## Phase 3: [US1] Deploy website content for embedding (Priority: P1)
- [X] T009 [US1] Create content_parser.py service with URL fetching and HTML parsing functionality
- [X] T010 [US1] Implement content chunking logic in content_parser.py (1000 words per chunk)
- [X] T011 [US1] Add content validation and sanitization to content_parser.py
- [X] T012 [US1] Create unit tests for content parsing functionality
- [ ] T013 [US1] Test: Verify content can be fetched from URL and parsed correctly

## Phase 4: [US2] Generate text embeddings using Cohere (Priority: P1)
- [X] T014 [US2] Create embedding_generator.py service with Cohere API integration
- [X] T015 [US2] Implement embedding generation with proper error handling for Cohere API
- [X] T016 [US2] Add embedding validation (vector size consistency)
- [X] T017 [US2] Handle rate limiting and API errors for Cohere
- [X] T018 [US2] Create unit tests for embedding generation
- [ ] T019 [US2] Test: Verify text content can be converted to embeddings with consistent dimensions

## Phase 5: [US3] Store embeddings in Qdrant vector database (Priority: P1)
- [X] T020 [US3] Create qdrant_service.py with Qdrant client integration
- [X] T021 [US3] Implement embedding storage in Qdrant with unique IDs
- [X] T022 [US3] Add embedding retrieval functionality from Qdrant
- [X] T023 [US3] Handle Qdrant connection errors and retry logic
- [X] T024 [US3] Create unit tests for Qdrant operations
- [ ] T025 [US3] Test: Verify embeddings are stored and can be retrieved with minimal latency

## Phase 6: [US4] Document local and cloud setup (Priority: P2)
- [X] T026 [US4] Update README.md with detailed setup instructions
- [X] T027 [US4] Add API documentation based on contracts/embeddings-api.yaml
- [X] T028 [US4] Document environment variables and configuration options
- [X] T029 [US4] Add troubleshooting section for common issues
- [ ] T030 [US4] Test: Verify documentation enables environment reproduction within 30 minutes

## Phase 7: Integration and Main Function
- [X] T031 Create main.py with the primary workflow function: get URL → chunk content → generate embeddings → store in Qdrant
- [X] T032 Implement command-line argument parsing for main.py
- [X] T033 Add progress tracking and logging to main.py
- [X] T034 Create integration tests for the complete workflow
- [ ] T035 Test: Verify end-to-end functionality from URL to stored embeddings

## Phase 8: Polish & Cross-Cutting Concerns
- [X] T036 Add comprehensive error handling throughout the application
- [X] T037 Implement logging for debugging and monitoring
- [X] T038 Add input validation for all user-provided parameters
- [ ] T039 Create API endpoints based on contracts/embeddings-api.yaml
- [ ] T040 Add performance monitoring and metrics
- [ ] T041 Update documentation with API usage examples
- [X] T042 Run full test suite to ensure all functionality works correctly