# Deployment Guide: Render

This guide covers deploying the AI Study Notes Assistant on Render.com.

## Prerequisites

- Render account (https://render.com)
- GitHub repository with the project
- OpenAI API key

## Step 1: Prepare Repository

1. Create a `.gitignore` file:
```
.env
.env.local
__pycache__/
*.pyc
.DS_Store
venv/
data/
logs/
.vscode/
.idea/
```

2. Create a `render.yaml` file in the root directory:

```yaml
services:
  - type: web
    name: ai-study-backend
    env: python
    plan: standard
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: OPENAI_MODEL
        value: gpt-4
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
      - key: CHROMA_DB_PATH
        value: /var/data/chroma_db
      - key: UPLOAD_FOLDER
        value: /var/data/uploads
    disks:
      - name: data
        mountPath: /var/data
        sizeGB: 10

  - type: web
    name: ai-study-frontend
    env: python
    plan: standard
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: BACKEND_URL
        value: https://ai-study-backend.onrender.com
```

## Step 2: Connect to Render

1. Go to https://dashboard.render.com
2. Click "New +"
3. Select "Web Service"
4. Connect your GitHub repository
5. Choose the repository and branch

## Step 3: Configure Backend Service

1. Service name: `ai-study-backend`
2. Environment: Python 3
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Environment Variables

Add these variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: gpt-4
- `ENVIRONMENT`: production
- `DEBUG`: false

### Disk Configuration

Add a persistent disk:
- Mount path: `/var/data`
- Size: 10 GB

## Step 4: Configure Frontend Service

1. Service name: `ai-study-frontend`
2. Environment: Python 3
3. Build command: `pip install -r requirements.txt`
4. Start command: `streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0`

### Environment Variables

- `BACKEND_URL`: https://ai-study-backend.onrender.com

## Step 5: Deploy

1. Click "Create Web Service"
2. Monitor deployment in the dashboard
3. Once deployed, your services will be available at:
   - Backend: https://ai-study-backend.onrender.com
   - Frontend: https://ai-study-frontend.onrender.com

## Step 6: Monitor

Monitor logs and performance in the Render dashboard. Use Render's built-in monitoring to track:
- CPU usage
- Memory usage
- Response times
- Error rates

## Scaling

For production with high traffic:

1. Upgrade to higher tier (Standard → Premium → Pro)
2. Enable auto-scaling
3. Add caching layer (Redis)
4. Consider database optimization

## Costs

As of 2024:
- Web Service: $7-70/month (depending on tier)
- Persistent Disk: $0.25/GB/month
- Estimated: $15-30/month for small-medium usage

## Troubleshooting

### Service won't start
- Check logs in Render dashboard
- Verify `requirements.txt` is present
- Ensure environment variables are set

### Slow responses
- Check API rate limits (OpenAI)
- Monitor vector store size
- Consider caching

### Data persistence issues
- Verify disk is attached
- Check disk usage in dashboard
- Ensure permissions are correct

## Backup and Recovery

1. Download data regularly from persistent disk
2. Store in secure cloud storage
3. Implement daily automated backups

```bash
# Download backup
render backup download-data ai-study-backend
```

## Next Steps

- Set up monitoring and alerting
- Configure custom domain
- Implement CI/CD pipeline
- Set up error tracking (Sentry)
