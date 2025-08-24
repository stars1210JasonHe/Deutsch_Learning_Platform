# 🚀 NAS Frontend Deployment Guide

Complete guide for deploying your language learning app with frontend + backend on Synology NAS.

## 📋 Quick Setup Checklist

- [ ] Build frontend locally
- [ ] Copy files to NAS
- [ ] Fix .env file (remove comments)
- [ ] Use correct main.py for static serving
- [ ] Deploy Docker container on port 7777

## 🏗️ Step-by-Step Deployment

### 1. Build Frontend Locally (Windows)

```bash
# On your Windows machine
cd E:/LanguageLearning/frontend
npm run build
```

### 2. Copy Project to NAS

```bash
# Copy entire project to NAS
scp -r E:/LanguageLearning/* root@your-nas-ip:/volume1/docker/Deutsch_Learning_Platform/
```

### 3. Fix Environment Variables

**CRITICAL**: Remove all comments from .env file values!

```bash
# On NAS, edit .env file
vi /volume1/docker/Deutsch_Learning_Platform/.env

# ❌ WRONG:
OPENAI_IMAGE_API_KEY=sk-proj-abc123...  # Direct OpenAI for images

# ✅ CORRECT:
OPENAI_IMAGE_API_KEY=sk-proj-abc123...
```

### 4. Use Correct Main.py for Static Serving

```bash
# Copy the NAS-specific main.py that serves frontend
cp app/main_nas.py app/main.py
```

The `main_nas.py` file includes:
- ✅ Static file serving: `app.mount("/", StaticFiles(...))`
- ✅ Dual API routes: Both `/api/auth/*` and `/auth/*`
- ❌ No conflicting root route

### 5. Deploy Container

```bash
cd /volume1/docker/Deutsch_Learning_Platform

# Build image
docker build -t vibe-deutsch:latest .

# Run container on port 7777
docker run -d \
  --name vibe-deutsch \
  --restart unless-stopped \
  -p 7777:8000 \
  -v /volume1/docker/Deutsch_Learning_Platform/data:/app/data \
  -v /volume1/docker/Deutsch_Learning_Platform/.env:/app/.env:ro \
  --env-file .env \
  vibe-deutsch:latest
```

### 6. Verify Deployment

```bash
# Test backend health
curl http://localhost:7777/health

# Test frontend (should return HTML, not JSON)
curl http://localhost:7777/

# Check logs
docker logs vibe-deutsch --tail 20

# Access from browser
# http://your-nas-ip:7777
```

## 🔧 Troubleshooting

### Frontend Shows API Response Instead of App

**Problem**: Visiting `/` shows `{"message":"Vibe Deutsch API"...}` instead of the Vue app.

**Solution**: 
- Make sure you're using `main_nas.py` as `main.py`
- Verify static files exist: `docker exec vibe-deutsch ls /app/frontend/dist/`
- Check no conflicting root route exists

### API Calls Return 404/405 Errors

**Problem**: Frontend can't reach backend API endpoints.

**Solution**: The `main_nas.py` includes both route patterns:
- `/auth/login` (for development with Vite proxy)
- `/api/auth/login` (for production direct calls)

### Environment Variables Not Loading

**Problem**: API keys return 401 errors.

**Solutions**:
1. **Remove comments from .env values** (most common issue)
2. **Recreate container** (don't just restart):
   ```bash
   docker stop vibe-deutsch && docker rm vibe-deutsch
   docker run -d --name vibe-deutsch ...
   ```
3. **Check file exists**: `cat .env | grep OPENAI_API_KEY`

### Docker Build Cache Issues

**Problem**: Changes not reflected in container.

**Solution**: Force clean rebuild:
```bash
docker stop vibe-deutsch && docker rm vibe-deutsch
docker rmi vibe-deutsch:latest
docker build --no-cache -t vibe-deutsch:latest .
```

### Port Conflicts

**Problem**: Port 7777 already in use.

**Solution**: Change port mapping:
```bash
# Use different port (e.g., 8888)
-p 8888:8000
```

## 📊 Monitoring

### Check Container Status
```bash
docker ps | grep vibe-deutsch
docker logs vibe-deutsch --tail 50
docker stats vibe-deutsch
```

### Check API Endpoints
```bash
curl http://localhost:7777/docs         # API documentation
curl http://localhost:7777/health       # Health check
curl http://localhost:7777/api/auth/me  # Test API route
```

### Check Frontend Assets
```bash
docker exec vibe-deutsch ls -la /app/frontend/dist/
docker exec vibe-deutsch ls -la /app/frontend/dist/assets/
```

## 🚀 Success Indicators

When deployment is successful, you should see:

**✅ Container Logs:**
```
INFO: Started server process [11]
INFO: Application startup complete.  
INFO: Uvicorn running on http://0.0.0.0:8000
GET / HTTP/1.1 200 OK
GET /assets/index-xxx.js HTTP/1.1 200 OK
POST /api/auth/login HTTP/1.1 200 OK
```

**✅ Browser Access:**
- `http://your-nas-ip:7777` shows your Vue app
- Login works without 401/404 errors
- All features functional

## 🔄 Update Workflow

When you make changes:

1. **Frontend changes**: Build locally + copy dist files + rebuild container
2. **Backend changes**: Copy Python files + rebuild container  
3. **Config changes**: Edit .env + recreate container (don't just restart)

## 🎯 Quick Commands Reference

```bash
# Full redeploy
docker stop vibe-deutsch && docker rm vibe-deutsch
docker build -t vibe-deutsch:latest .
docker run -d --name vibe-deutsch --restart unless-stopped -p 7777:8000 -v /volume1/docker/Deutsch_Learning_Platform/data:/app/data -v /volume1/docker/Deutsch_Learning_Platform/.env:/app/.env:ro --env-file .env vibe-deutsch:latest

# Check everything is working
curl http://localhost:7777/health
curl http://localhost:7777/ | head -5

# View logs
docker logs vibe-deutsch --tail 20 -f
```

---

## 📝 Notes

- **Always remove comments from .env file values** - this is the #1 cause of issues
- **Use main_nas.py** - it handles both API route patterns 
- **Recreate container for .env changes** - restart isn't enough
- **Frontend and backend run on same port (7777)** - no separate nginx needed

🎉 **Your German learning platform should now be running at `http://your-nas-ip:7777`!**