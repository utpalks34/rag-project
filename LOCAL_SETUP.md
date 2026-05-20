# Local Setup Guide

Get the AI Study Notes Assistant running on your local machine.

## Prerequisites

- Python 3.11+
- pip or conda
- OpenAI API key
- Git (optional)

## Installation

### Step 1: Clone or Download

```bash
# Clone repository
git clone <repository-url>
cd "Ai study notes"

# Or extract downloaded ZIP file
```

### Step 2: Create Virtual Environment

**Using venv:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

**Using conda:**
```bash
conda create -n ai-study python=3.11
conda activate ai-study
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (backend)
- Streamlit (frontend)
- LangChain & OpenAI
- ChromaDB (vector database)
- PyPDF (PDF processing)
- And all utilities

### Step 4: Configure Environment

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4
ENVIRONMENT=development
DEBUG=true
```

3. Verify other settings:
```
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
```

## Running the Application

### Option 1: Terminal 1 for Backend, Terminal 2 for Frontend

**Terminal 1 - Backend:**
```bash
# Activate venv first
cd "Ai study notes"
source venv/bin/activate  # or venv\Scripts\activate on Windows

uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Terminal 2 - Frontend:**
```bash
# Activate venv first
cd "Ai study notes"
source venv/bin/activate  # or venv\Scripts\activate on Windows

streamlit run frontend/app.py
```

You should see:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### Option 2: Using Docker Compose

```bash
# Create .env file with OPENAI_API_KEY

# Start services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

Services will be available at:
- Backend: http://localhost:8000
- Frontend: http://localhost:8501
- API Docs: http://localhost:8000/docs

## Verification

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"...","database_connected":true,"api_key_configured":true}

# API documentation
# Visit http://localhost:8000/docs
```

### Test Frontend

1. Open http://localhost:8501
2. Check sidebar for API connection status
3. Should show green "✓ Connected"

## First Run

1. **Upload a PDF:**
   - Go to "Upload" tab
   - Select a PDF file
   - Wait for processing

2. **Ask a Question:**
   - Go to "Chat" tab
   - Type your question
   - View the answer with sources

3. **Monitor:**
   - Check logs in terminal
   - View response times
   - Check confidence scores

## Troubleshooting

### ModuleNotFoundError

```bash
# Make sure venv is activated
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

### Connection Refused

```
Error: Connection refused to http://localhost:8000
```

Make sure backend is running:
```bash
# In a new terminal
uvicorn backend.main:app --reload
```

### OPENAI_API_KEY not found

```bash
# Verify .env file exists and has correct format
cat .env  # or type .env on Windows

# Should show:
# OPENAI_API_KEY=sk-...
```

### No modules available for ChromaDB

```bash
# Update packages
pip install --upgrade chromadb

# Or reinstall
pip uninstall chromadb
pip install chromadb==0.4.18
```

### Streamlit cache errors

```bash
# Clear Streamlit cache
streamlit cache clear
```

## Development Tips

### Enable Hot Reload

Backend already has `--reload` flag. For frontend:
```bash
streamlit run frontend/app.py --logger.level=debug
```

### Monitor Database

```bash
# Check ChromaDB collection
python -c "
from vector_store.vector_db import VectorStore
from config import settings

vs = VectorStore(settings.chroma_db_path)
print(vs.get_collection_stats())
"
```

### View Logs

```bash
# Real-time logs
tail -f logs/app.log

# Error logs only
tail -f logs/error.log
```

### Test RAG Pipeline

```bash
python -c "
from rag_pipeline.pipeline import RAGPipeline

rag = RAGPipeline()
response = rag.answer_question('What is photosynthesis?')
print(response['answer'])
"
```

## Performance Optimization

### Reduce Startup Time

1. Skip query rewriting:
```env
ENABLE_QUERY_REWRITING=false
```

2. Reduce chunk overlap:
```env
CHUNK_OVERLAP=25
```

### Improve Response Time

1. Enable caching:
```env
ENABLE_CACHE=true
CACHE_TTL=3600
```

2. Reduce top_k results:
```env
TOP_K_RESULTS=3
```

## Common Issues & Solutions

### Issue: Slow embedding generation
**Solution:** Batch embeddings are already implemented. Check OpenAI rate limits.

### Issue: High memory usage
**Solution:** Reduce `BATCH_SIZE` in .env or limit vector store size

### Issue: PDF processing fails
**Solution:** Ensure PDF is not corrupted. Try with a simple PDF first.

### Issue: "Too many requests" from OpenAI
**Solution:** Increase wait time between requests or upgrade API plan

## Next Steps

1. Try with different PDFs
2. Explore API endpoints at http://localhost:8000/docs
3. Customize UI in `frontend/app.py`
4. Modify RAG parameters in `config.py`
5. Deploy to Render or AWS when ready

## File Structure Reference

```
Ai study notes/
├── backend/
│   └── main.py              # FastAPI application
├── frontend/
│   └── app.py               # Streamlit app
├── rag_pipeline/
│   ├── chunker.py           # Document chunking
│   ├── pipeline.py          # Main RAG logic
│   └── query_rewriter.py    # Query enhancement
├── vector_store/
│   └── vector_db.py         # ChromaDB interface
├── utils/
│   ├── logger.py            # Logging
│   ├── pdf_processor.py     # PDF extraction
│   ├── models.py            # Data models
│   ├── exceptions.py        # Error handling
│   └── helpers.py           # Utilities
├── data/
│   ├── uploads/             # Uploaded PDFs
│   └── chroma_db/           # Vector database
├── logs/                    # Application logs
├── docker/                  # Docker configs
├── config.py                # Configuration
├── requirements.txt         # Dependencies
└── .env                     # Environment variables
```

## Support

For issues or questions:
1. Check logs in `logs/app.log`
2. Review .env configuration
3. Verify OpenAI API key validity
4. Check internet connection for API calls
