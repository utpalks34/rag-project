# Quick Reference Guide

## 🚀 Most Common Tasks

### Start Local Development (2 minutes)

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add OPENAI_API_KEY=sk-your-key

# Run (2 terminals)
# Terminal 1:
uvicorn backend.main:app --reload

# Terminal 2:
streamlit run frontend/app.py

# Visit http://localhost:8501
```

### Docker Quick Start (1 minute)

```bash
# Setup
cp .env.example .env
# Edit .env with your OpenAI API key

# Run
docker-compose -f docker/docker-compose.yml up

# Access at http://localhost:8501
```

### Query the API (curl)

```bash
# Upload a PDF
curl -X POST http://localhost:8000/api/upload \
  -F "file=@study_guide.pdf"

# Ask a question
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is photosynthesis?",
    "top_k": 5,
    "include_sources": true
  }'

# Get chat history
curl http://localhost:8000/api/chat/history

# Check health
curl http://localhost:8000/health
```

### API Documentation

```
# Interactive API docs:
http://localhost:8000/docs

# Alternative docs:
http://localhost:8000/redoc
```

---

## 📁 File Locations

| What | Where |
|------|-------|
| Configuration | `.env` |
| Backend code | `backend/main.py` |
| Frontend code | `frontend/app.py` |
| RAG pipeline | `rag_pipeline/` |
| Vector store | `vector_store/` |
| Utilities | `utils/` |
| Uploaded PDFs | `data/uploads/` |
| Embeddings DB | `data/chroma_db/` |
| Logs | `logs/app.log` |
| Tests | `tests/` |
| Docker config | `docker/` |

---

## ⚙️ Configuration Quick Edits

### Change chunk size
Edit `.env`:
```
CHUNK_SIZE=512          # Change this number
```

### Change number of results
Edit `.env`:
```
TOP_K_RESULTS=5         # Return 5 chunks per query
```

### Enable/disable features
Edit `.env`:
```
ENABLE_QUERY_REWRITING=true    # Query expansion
ENABLE_HYBRID_SEARCH=true      # Semantic + keyword
ENABLE_CACHE=true              # Caching
```

### Change log level
Edit `.env`:
```
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_rag_pipeline.py

# With verbose output
pytest -v

# With coverage
pytest --cov=.

# Run quick test
python -m pytest tests/test_rag_pipeline.py::TestDocumentChunker::test_chunk_text_basic
```

---

## 📊 Monitoring

### View logs
```bash
# All logs
tail -f logs/app.log

# Only errors
tail -f logs/error.log

# Last 50 lines
tail -50 logs/app.log
```

### Check API stats
```bash
curl http://localhost:8000/stats | python -m json.tool
```

### Health check
```bash
curl http://localhost:8000/health | python -m json.tool
```

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Activate venv, run `pip install -r requirements.txt` |
| `Connection refused` | Backend not running, start with `uvicorn backend.main:app --reload` |
| `OPENAI_API_KEY not found` | Check `.env` file has correct key format `sk-...` |
| `Slow responses` | Reduce `TOP_K_RESULTS` or `CHUNK_SIZE` in `.env` |
| `High memory usage` | Reduce `BATCH_SIZE` or limit concurrent queries |
| `PDF won't upload` | Check file is valid PDF, < 50MB, and readable |

---

## 🚀 Deployment

### Quick Deploy to Render
See `DEPLOYMENT_RENDER.md` for detailed steps. Summary:
1. Push code to GitHub
2. Connect to Render
3. Add `OPENAI_API_KEY` env var
4. Deploy (auto-deploys on push)

### Deploy to AWS
See `DEPLOYMENT_AWS.md` for detailed steps. Summary:
1. Build Docker images
2. Push to ECR
3. Create ECS cluster
4. Configure load balancer
5. Deploy services

### Local Docker
```bash
docker-compose -f docker/docker-compose.yml up -d
```

---

## 💻 Code Examples

### Python Client
```python
import requests

# Upload
files = {"file": open("doc.pdf", "rb")}
r = requests.post("http://localhost:8000/api/upload", files=files)
print(r.json())

# Query
payload = {"query": "What is photosynthesis?", "top_k": 5}
r = requests.post("http://localhost:8000/api/query", json=payload)
print(r.json()["answer"])

# History
r = requests.get("http://localhost:8000/api/chat/history")
print(r.json()["messages"])
```

### cURL Examples
```bash
# Upload
curl -F "file=@study.pdf" http://localhost:8000/api/upload

# Query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Your question here?"}'

# Clear history
curl -X POST http://localhost:8000/api/chat/clear
```

---

## 📚 Documentation Map

| Document | Purpose |
|----------|---------|
| `README.md` | Project overview |
| `LOCAL_SETUP.md` | Local development |
| `DEPLOYMENT_RENDER.md` | Deploy on Render |
| `DEPLOYMENT_AWS.md` | Deploy on AWS |
| `ARCHITECTURE.md` | System design |
| `PRODUCTION_CHECKLIST.md` | Pre-deployment |
| `API_EXAMPLES.py` | Code examples |
| `PROJECT_DELIVERY.md` | Project summary |

---

## 🎯 Quick Workflow

### 1. First Time Setup
```bash
git clone <repo>
cd "Ai study notes"
cp .env.example .env  # Edit with API key
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Daily Development
```bash
source venv/bin/activate
# Terminal 1: uvicorn backend.main:app --reload
# Terminal 2: streamlit run frontend/app.py
```

### 3. Test Changes
```bash
pytest tests/
```

### 4. Deploy
```bash
# Option A: Docker
docker-compose -f docker/docker-compose.yml up

# Option B: Production
# Follow DEPLOYMENT_RENDER.md or DEPLOYMENT_AWS.md
```

---

## 🔐 Security Reminders

- ✅ Never commit `.env` with real API keys
- ✅ Use `.env.example` as template
- ✅ Rotate API keys periodically
- ✅ Enable HTTPS in production
- ✅ Use strong SECRET_KEY
- ✅ Validate all user inputs
- ✅ Log security events
- ✅ Monitor for suspicious activity

---

## 📈 Performance Tips

- Set `ENABLE_CACHE=true` for repeated queries
- Use `CHUNK_SIZE=512` for optimal speed/quality
- Reduce `TOP_K_RESULTS` if slow
- Use `ENABLE_HYBRID_SEARCH=true` for better results
- Monitor response times in logs
- Use batch operations for bulk uploads

---

## 🐛 Debug Mode

Enable debug logging:
```bash
# Edit .env
DEBUG=true
LOG_LEVEL=DEBUG
```

View detailed logs:
```bash
# Watch real-time
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# Find specific queries
grep "photosynthesis" logs/app.log
```

---

## 📞 Quick Help

### API Health
```bash
curl http://localhost:8000/health
```

### View API Docs
```
http://localhost:8000/docs
```

### Check Logs
```bash
tail -f logs/app.log
```

### Restart Services
```bash
# Local
Ctrl+C in both terminals, then restart

# Docker
docker-compose -f docker/docker-compose.yml restart
```

### Clear Cache
```bash
python -c "from utils.helpers import cache_utils; cache_utils.clear()"
```

---

## 🎓 Learning Path

1. **Week 1**: Local setup and basic usage
2. **Week 2**: Explore API endpoints
3. **Week 3**: Customize configuration
4. **Week 4**: Deploy to cloud

---

## 📋 Checklist for Production

```
☐ Environment variables configured
☐ OPENAI_API_KEY set
☐ API key is valid (test health endpoint)
☐ All tests passing
☐ No errors in logs
☐ Response time < 2 seconds
☐ All documentation read
☐ Pre-deployment checklist reviewed
☐ Monitoring configured
☐ Backup strategy in place
```

---

**Last Updated:** May 2024  
**Version:** 1.0.0

For more details, see the full documentation in the project root.
