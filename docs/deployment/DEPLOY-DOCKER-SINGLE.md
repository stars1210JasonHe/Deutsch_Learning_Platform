# 🐳 Single Docker Container Deployment Guide

Complete guide for deploying Vibe Deutsch on Synology NAS using a single Docker container (without docker-compose).

## 🎯 Prerequisites

- Synology NAS with Docker package installed
- SSH access enabled (optional)
- At least 2GB free RAM
- Custom port of your choice (we'll use 9876)

## 🚀 Deployment Methods

### Method 1: SSH Command Line (Recommended)

#### Step 1: Copy Project to NAS
```bash
# Copy your project to NAS
scp -r /path/to/LanguageLearning admin@your-nas-ip:/volume1/docker/vibe-deutsch/

# Or use File Station to upload files
```

#### Step 2: SSH into NAS and Deploy
```bash
# SSH into your NAS
ssh admin@your-nas-ip

# Navigate to project directory
cd /volume1/docker/vibe-deutsch

# Configure environment
cp .env.example .env
nano .env  # Edit with your API keys

# Make scripts executable
chmod +x docker-run.sh docker-stop.sh

# Deploy with custom port (9876)
./docker-run.sh
```

### Method 2: Container Manager GUI

#### Step 1: Build Image
1. Open **Container Manager**
2. Go to **Image** tab
3. Click **Add** → **Add from Dockerfile**
4. Set path: `/docker/vibe-deutsch`
5. Image name: `vibe-deutsch:latest`
6. Click **Build**

#### Step 2: Create Container
1. Go to **Container** tab
2. Click **Create**
3. **Image**: Select `vibe-deutsch:latest`
4. **Container name**: `vibe-deutsch`
5. **Port Settings**:
   - Local Port: `9876` (your custom port)
   - Container Port: `8000`
6. **Volume Settings**:
   - `/docker/vibe-deutsch/data` → `/app/data`
   - `/docker/vibe-deutsch/.env` → `/app/.env` (read-only)
7. **Environment Variables**:
   ```
   OPENAI_API_KEY=your_api_key
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   OPENAI_MODEL=openai/gpt-4o-mini
   SECRET_KEY=your_secret_key
   ```
8. **Resource Limits**:
   - Memory: 4GB
   - CPU: 2 cores
9. Click **Apply**

## ⚙️ Custom Port Configuration

### Change Port in Scripts
Edit `docker-run.sh` and change this line:
```bash
HOST_PORT="YOUR_PREFERRED_PORT"  # Change 9876 to your port
```

### Popular Non-Standard Port Options
- **9876** (default in script)
- **7777**
- **8765**  
- **9999**
- **5555**

## 🔧 Management Commands

### Start/Stop Container
```bash
# Start (deploy)
./docker-run.sh

# Stop
./docker-stop.sh

# View logs
docker logs vibe-deutsch

# Check status
docker ps

# Access container shell
docker exec -it vibe-deutsch bash
```

### Manual Docker Commands
```bash
# Build image
docker build -t vibe-deutsch:latest .

# Run container with custom port
docker run -d \
  --name vibe-deutsch \
  --restart unless-stopped \
  -p 9876:8000 \
  -v /volume1/docker/vibe-deutsch/data:/app/data \
  -v /volume1/docker/vibe-deutsch/.env:/app/.env:ro \
  --env-file .env \
  --memory=4g \
  --cpus=2.0 \
  vibe-deutsch:latest

# Stop container
docker stop vibe-deutsch

# Remove container
docker rm vibe-deutsch
```

## 📊 Monitoring & Maintenance

### Check Application Status
```bash
# Container status
docker ps | grep vibe-deutsch

# Application logs
docker logs -f vibe-deutsch

# Resource usage
docker stats vibe-deutsch

# Health check
curl http://your-nas-ip:9876/docs
```

### Backup & Updates
```bash
# Backup database
docker exec vibe-deutsch cp /app/data/app.db /app/data/backup_$(date +%Y%m%d).db

# Update application
./docker-stop.sh
git pull  # or copy new files
./docker-run.sh
```

## 🛡️ Security Configuration

### Firewall Settings
1. Open **Control Panel** → **Security** → **Firewall**
2. **Create rule** for your custom port (9876)
3. **Allow** access from trusted IPs only

### Port Access Control
```bash
# Check if port is open
netstat -tulpn | grep :9876

# Test external access
curl http://your-nas-ip:9876/docs
```

## ⚠️ Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker logs vibe-deutsch

# Check if port is available
netstat -tulpn | grep :9876

# Verify .env file
cat .env
```

#### Port Conflicts
```bash
# Find process using port
sudo lsof -i :9876

# Use different port
# Edit docker-run.sh and change HOST_PORT
```

#### Permission Issues
```bash
# Fix data directory permissions
sudo chmod 755 /volume1/docker/vibe-deutsch/data
sudo chown -R admin:users /volume1/docker/vibe-deutsch/data
```

#### Build Failures
```bash
# Clean Docker cache
docker system prune -a

# Rebuild image
docker build --no-cache -t vibe-deutsch:latest .
```

### Performance Issues
```bash
# Check memory usage
docker stats vibe-deutsch

# Restart container
docker restart vibe-deutsch

# Increase memory limit
# Edit docker-run.sh and change --memory=4g to --memory=6g
```

## 🎯 Access Your Application

After successful deployment:

**URL**: `http://your-nas-ip:9876`

**Example**: `http://192.168.1.100:9876`

### Test Endpoints
- **Main App**: `http://your-nas-ip:9876`
- **API Docs**: `http://your-nas-ip:9876/docs`
- **Health Check**: `http://your-nas-ip:9876/auth/me`

## 🚀 Success Checklist

- [ ] Project copied to `/volume1/docker/vibe-deutsch/`
- [ ] `.env` file configured with API keys
- [ ] Custom port chosen (9876 or your preference)
- [ ] Docker image built successfully
- [ ] Container running and healthy
- [ ] Application accessible at custom port
- [ ] Database persisting in `/data` volume

---

🎉 **Congratulations!** Your German learning platform is now running on port 9876!