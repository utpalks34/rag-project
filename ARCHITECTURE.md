# Architecture Documentation

## System Design Philosophy

This application follows clean architecture principles with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│           Presentation Layer                    │
│  - Streamlit Frontend                           │
│  - User interaction & visualization             │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│           API Layer                             │
│  - FastAPI endpoints                            │
│  - Request/response handling                    │
│  - Input validation                             │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│           Business Logic Layer                  │
│  - RAG Pipeline                                 │
│  - Document processing                          │
│  - Query handling                               │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│           Data Access Layer                     │
│  - Vector Store                                 │
│  - PDF Processing                               │
│  - File Management                              │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│           Infrastructure                        │
│  - ChromaDB                                     │
│  - File System                                  │
│  - Logging                                      │
└─────────────────────────────────────────────────┘
```

## Component Descriptions

### 1. Frontend (Streamlit)

**File:** `frontend/app.py`

**Responsibilities:**
- User interface for document upload
- Chat interface for queries
- Display of results with source citations
- Theme customization (dark/light)
- Session state management

**Key Features:**
- Multi-tab interface (Upload, Chat, Sources)
- Real-time chat display
- Confidence score visualization
- Source citation display
- Settings panel

**Why Streamlit?**
- Rapid development without complex frontend frameworks
- Built-in chat UI components
- Session state management
- No deployment complexity
- Perfect for prototyping and POC

### 2. Backend (FastAPI)

**File:** `backend/main.py`

**Responsibilities:**
- API endpoint routing
- Request/response handling
- Middleware configuration
- Error handling
- Startup/shutdown management

**Key Features:**
- Async request handling
- Automatic API documentation
- CORS middleware
- Request ID tracking
- Comprehensive error handling

**Why FastAPI?**
- Built-in async support for concurrent requests
- Automatic Swagger UI documentation
- Pydantic integration for validation
- High performance (comparable to Node.js)
- Type hints for better code quality

### 3. RAG Pipeline

**File:** `rag_pipeline/pipeline.py`

**Responsibilities:**
- Document processing orchestration
- Query handling and retrieval
- Answer generation using LLM
- Chat history management
- Statistics tracking

**Flow:**
```
Document Upload
    ↓
Extract Text (PDF Processor)
    ↓
Chunk Text (Semantic Chunking)
    ↓
Generate Embeddings (OpenAI)
    ↓
Store in Vector DB (ChromaDB)
    ↓
User Query
    ↓
Retrieve Relevant Chunks
    ↓
Generate Answer (GPT-4)
    ↓
Return with Sources & Scores
```

### 4. Document Chunker

**File:** `rag_pipeline/chunker.py`

**Responsibilities:**
- Text splitting using RecursiveCharacterTextSplitter
- Metadata preservation
- Page tracking

**Key Design Decisions:**

**RecursiveCharacterTextSplitter Algorithm:**
```
Input: Full text with separators ["\n\n", "\n", ". ", " ", ""]

1. Try splitting on first separator ("\n\n")
2. If chunks > chunk_size:
   - Recursively split on next separator
3. Repeat until chunks fit within chunk_size
4. Add overlap between chunks

Advantages:
- Preserves semantic meaning
- Handles hierarchical structures
- Better context retention
- Configurable for different document types

Overhead:
- Slightly slower than naive splitting
- Negligible for <50K chunks
- Worth the better quality
```

**Configuration:**
- `chunk_size=512`: Optimal for GPT-4 context windows
- `chunk_overlap=50`: Ensures context continuity between chunks
- Separators: Prioritize semantic boundaries

### 5. Vector Store (ChromaDB)

**File:** `vector_store/vector_db.py`

**Responsibilities:**
- Persistent embedding storage
- Similarity search (cosine distance)
- Metadata filtering
- Hybrid retrieval

**Architecture:**

```
ChromaDB Collection
├── Documents (chunks of text)
├── Embeddings (1536-dim vectors)
├── Metadata (source, page, chunk_index)
└── IDs (unique identifiers)

Search Methods:
1. Semantic Search (default)
   - Uses cosine similarity
   - Vector: chunk_text → embedding → search
   
2. Hybrid Search (optional)
   - Combines semantic (70%) + keyword (30%)
   - Better recall and precision
   - Slower but more accurate

3. Keyword Search
   - Simple term overlap
   - Fast but less semantically aware
```

**Why ChromaDB?**
- Persistent storage without external DB
- Built-in similarity search
- Metadata filtering
- Lightweight and embeddable
- Perfect for small-medium deployments

**Alternative Considerations:**
- **Pinecone**: Cloud-based, managed, but costs more
- **Weaviate**: More complex, better for large-scale
- **Milvus**: Open-source, better scalability
- **Qdrant**: Modern, feature-rich, good middle ground

### 6. Query Rewriter

**File:** `rag_pipeline/query_rewriter.py`

**Responsibilities:**
- Query expansion and rewriting
- Keyword extraction
- Query optimization for retrieval

**Techniques:**

```
Original Query: "What is photosynthesis?"

1. Question to Statement:
   "What is photosynthesis?" → "Photosynthesis"

2. Synonym Expansion:
   "process" → also search for "method", "procedure"
   "what" → also search for "how", "explain"

3. Keyword Extraction:
   Extract: ["photosynthesis", "process", "plants"]
   
4. Multiple Queries:
   Search with multiple variations
   Combine and rank results

Benefits:
- Handles ambiguous queries
- Improves recall
- Handles synonyms
- Better context understanding
```

### 7. PDF Processor

**File:** `utils/pdf_processor.py`

**Responsibilities:**
- PDF file handling
- Text extraction with page tracking
- File validation and management

**Text Extraction:**
```python
PdfReader(file_path)
├── For each page:
│   ├── Extract text
│   ├── Track page number
│   └── Preserve structure
├── Combine all pages
└── Return with page mapping
```

### 8. Error Handling

**File:** `utils/exceptions.py`

**Exception Hierarchy:**
```
AIAssistantException
├── PDFProcessingError
├── VectorStoreError
├── RAGPipelineError
└── OpenAIError

Response Format:
{
  "error": "Error Type",
  "detail": "Human-readable message",
  "request_id": "UUID for tracking",
  "timestamp": "ISO 8601"
}
```

**Error Handling Strategy:**
1. Specific exceptions for different components
2. Request ID tracking for debugging
3. Graceful degradation
4. User-friendly error messages
5. Comprehensive logging

### 9. Configuration Management

**File:** `config.py`

**Principles:**
- Environment-based configuration
- Type-safe with Pydantic
- Defaults for development
- Override via environment variables
- Auto-creation of directories

**Configuration Hierarchy:**
```
1. Environment variables (.env file)
2. Pydantic defaults
3. Fallback hardcoded defaults
```

### 10. Logging

**File:** `utils/logger.py`

**Strategy:**
- Structured logging with loguru
- Separate log files for errors
- Rotating logs to prevent disk bloat
- Console output for development
- File output for production

**Log Levels:**
```
DEBUG   - Development details
INFO    - Application flow
WARNING - Potential issues
ERROR   - Errors that don't stop execution
CRITICAL - Fatal errors
```

## Performance Considerations

### 1. Embedding Generation

**Current Approach:**
- Batch processing (default batch_size=32)
- Uses text-embedding-3-small (fast + accurate)
- Cost: ~$0.02 per million tokens

**Optimization:**
```python
# Process multiple documents together
documents = [doc1, doc2, doc3]
embeddings = embeddings_model.embed_documents(documents)
# Faster than individual calls
```

### 2. Vector Search

**Time Complexity:**
- K-NN search: O(n) with HNSW index: O(log n)
- Cosine similarity: O(1536) per comparison
- Top-K retrieval: O(n log k)

**Typical Performance:**
- 50,000 chunks: ~150ms search
- 500,000 chunks: ~300ms search
- 5,000,000 chunks: ~500ms search

### 3. LLM Calls

**Optimization Strategies:**
- Cache frequent queries
- Batch if possible
- Use faster models for pre-filtering
- Implement rate limiting

**Cost per Query:**
- Context retrieval: ~200 tokens
- Question: ~50 tokens
- Answer generation: ~300 tokens (avg)
- Total: ~550 tokens ≈ $0.02

## Scalability Architecture

### Vertical Scaling (Current)
- Single instance deployment
- Limited by machine resources
- Suitable for: <100 concurrent users

### Horizontal Scaling (Next)
```
Load Balancer
├── Backend Instance 1
├── Backend Instance 2
└── Backend Instance N

Shared Resources:
├── Vector Store (managed ChromaDB/Pinecone)
├── Cache (Redis)
└── Database (PostgreSQL)
```

### Database Sharding (Future)
```
Partition by:
- Collection ID
- Time range
- Hash(document_id)
```

## Security Architecture

### Data Protection
```
┌─────────────────────────────────┐
│ User Input                      │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ Input Validation & Sanitization │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ Authorization & Authentication  │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ Encryption & Hashing           │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│ Secure Storage                  │
└─────────────────────────────────┘
```

### Secrets Management
- Environment variables for secrets
- AWS Secrets Manager (production)
- Never log sensitive data
- Request IDs for audit trails

## Testing Strategy

### Unit Tests
```python
Test Components:
- Chunker logic
- Query rewriting
- Text processing
- Validation
```

### Integration Tests
```python
Test Flows:
- Document upload → storage
- Query → retrieval → answer
- Error scenarios
```

### E2E Tests
```
Test Complete Flows:
- Upload → Query → Answer
- Chat history management
- Source tracking
```

### Performance Tests
```
Measure:
- Response time
- Memory usage
- Vector search latency
- API throughput
```

## Deployment Strategies

### Development
- Single container
- Hot reload enabled
- Debug logging
- SQLite database

### Production
- Multi-container orchestration
- Health checks
- Auto-scaling
- Monitoring & alerts
- Backup & recovery

### High-Availability
```
Multiple Zones:
├── Zone 1
│  ├── Backend
│  ├── Vector Store replica
│  └── Cache
├── Zone 2
│  ├── Backend
│  ├── Vector Store replica
│  └── Cache
└── Zone 3
   └── Database primary
```

## Monitoring & Observability

### Metrics Collected
```
Application:
- Request count & latency
- Error rates
- Cache hit ratio
- Vector store stats

System:
- CPU usage
- Memory usage
- Disk I/O
- Network I/O
```

### Logging Strategy
```
Level 1: Application logs
- Entry/exit points
- Business logic decisions

Level 2: Debug logs
- Variable states
- Calculation steps

Level 3: Error logs
- Exceptions with full context
- Stack traces
```

### Alerting
```
Trigger when:
- Error rate > 1%
- Response time > 5s
- Memory usage > 80%
- Disk usage > 90%
```

## Future Enhancements

### Phase 2
- [ ] Multi-language support
- [ ] Advanced query understanding (NLU)
- [ ] Custom fine-tuned embeddings

### Phase 3
- [ ] Multi-document reasoning
- [ ] Metadata-based filtering
- [ ] Document clustering

### Phase 4
- [ ] Real-time collaboration
- [ ] Advanced analytics dashboard
- [ ] Custom LLM support

---

This architecture provides a solid foundation for a production-ready RAG application with room for scaling and enhancement.
