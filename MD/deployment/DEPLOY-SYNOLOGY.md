# 🐳 Synology NAS Deployment Guide

Complete guide for deploying Vibe Deutsch on Synology DS420+ using Docker.

## 📋 Prerequisites

### Synology NAS Requirements
- Synology DS420+ with DSM 7.0+
- Docker Package installed via Package Center
- At least 2GB RAM available
- 5GB free storage space

### Setup Steps on Synology

#### 1. Install Docker Package
1. Open **Package Center** on your Synology
2. Search for **Container Manager** (formerly Docker)
3. Install the package
4. Open **Container Manager**

#### 2. Enable SSH (Optional - for command line deployment)
1. Go to **Control Panel** → **Terminal & SNMP**
2. Enable **SSH service**
3. Note your NAS IP address

## 🚀 Deployment Methods

### Method 1: GUI Deployment (Recommended for beginners)

#### Step 1: Upload Project Files
1. Open **File Station**
2. Create folder: `/docker/vibe-deutsch/`
3. Upload your entire project to this folder
4. Ensure `.env` file contains your API keys

#### Step 2: Container Manager Setup
1. Open **Container Manager**
2. Go to **Project** tab
3. Click **Create**
4. Select **Create docker-compose.yml**
5. Set project path: `/docker/vibe-deutsch/`
6. Paste the docker-compose.yml content
7. Click **Next** → **Done**

#### Step 3: Environment Configuration
1. In Container Manager, find your project
2. Click **Action** → **Edit**
3. Go to **Environment** tab
4. Set these variables:
   ```
   OPENAI_API_KEY=your_api_key
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   OPENAI_MODEL=openai/gpt-4o-mini
   SECRET_KEY=your_32_character_secret
   ```

#### Step 4: Start Application
1. Click **Action** → **Build**
2. Wait for build to complete (5-10 minutes)
3. Click **Action** → **Up**
4. Access at: `http://your-nas-ip:8000`

### Method 2: SSH Command Line Deployment

#### Step 1: Connect via SSH
```bash
ssh admin@your-nas-ip
```

#### Step 2: Navigate and Setup
```bash
# Create project directory
sudo mkdir -p /volume1/docker/vibe-deutsch
cd /volume1/docker/vibe-deutsch

# Clone or upload your project
# (Upload via File Station or git clone)

# Create environment file
cp .env.example .env
nano .env  # Edit with your API keys
```

#### Step 3: Deploy
```bash
# Build and start
sudo docker-compose up -d

# Check status
sudo docker-compose ps

# View logs
sudo docker-compose logs -f
```

## 🔧 Configuration Files

### Environment Variables (.env)
```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
DATABASE_URL=sqlite:///./data/app.db
SECRET_KEY=your_very_long_secret_key_min_32_chars
```

### Port Configuration
- **Default**: Application runs on port 8000
- **Custom**: Modify `docker-compose.yml` ports section:
  ```yaml
  ports:
    - "9000:8000"  # Change 9000 to your preferred port
  ```

## 📊 Monitoring & Management

### Container Manager Dashboard
- **Status**: Monitor running containers
- **Resources**: Check CPU/Memory usage
- **Logs**: View application logs
- **Terminal**: Access container shell

### Health Checks
The container includes automatic health checks:
- Endpoint: `http://localhost:8000/docs`
- Interval: Every 30 seconds
- Timeout: 10 seconds

### Backup Strategy
```bash
# Backup database
sudo docker-compose exec vibe-deutsch cp /app/data/app.db /app/data/backup_$(date +%Y%m%d).db

# Backup entire data volume
sudo cp -r /volume1/docker/vibe-deutsch/data /volume1/docker/vibe-deutsch/backup_data_$(date +%Y%m%d)
```

## 🔍 Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
sudo docker-compose logs vibe-deutsch

# Common fixes:
# 1. Check .env file format
# 2. Verify port availability
# 3. Ensure sufficient disk space
```

#### Database Issues
```bash
# Reset database (WARNING: Deletes all data)
sudo docker-compose down
sudo rm -rf data/app.db
sudo docker-compose up -d
```

#### API Connection Issues
- Verify OPENAI_API_KEY in .env
- Check internet connectivity from NAS
- Confirm OpenRouter account has credits

#### Performance Issues
- Increase container memory limit in Container Manager
- Monitor CPU usage during AI operations
- Consider upgrading to faster storage

### Port Conflicts
If port 8000 is in use:
1. Edit `docker-compose.yml`
2. Change ports to `"8001:8000"`
3. Rebuild: `sudo docker-compose up -d --build`

### SSL/HTTPS Setup (Advanced)
For HTTPS access, consider:
1. Synology built-in reverse proxy
2. Let's Encrypt certificate
3. Custom domain setup

## 📈 Performance Optimization

### Resource Allocation
Recommended settings for DS420+:
- **CPU**: 50% limit (2 cores max)
- **Memory**: 1GB limit
- **Storage**: SSD cache if available

### Database Optimization
```bash
# Optimize database size
sudo docker-compose exec vibe-deutsch python scripts/checks/inspect_database.py

# Clean up old data
sudo docker-compose exec vibe-deutsch python scripts/fixes/cleanup_temp_files.py
```

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest code
cd /volume1/docker/vibe-deutsch
git pull

# Rebuild and restart
sudo docker-compose down
sudo docker-compose up -d --build
```

### Scheduled Maintenance
Set up DSM Task Scheduler for:
- Weekly database backups
- Monthly log cleanup
- Container health checks

## 🛡️ Security Considerations

### Network Security
- Use Synology firewall to restrict access
- Consider VPN for external access
- Change default ports if exposing to internet

### Data Protection
- Regular database backups
- Environment file encryption
- API key rotation

### Access Control
- Separate user accounts for application
- Minimal container permissions
- Regular security updates

## 📞 Support & Resources

### Log Locations
- Container logs: Container Manager → Logs tab
- Application logs: `/volume1/docker/vibe-deutsch/data/`
- System logs: DSM → Log Center

### Useful Commands
```bash
# Container shell access
sudo docker-compose exec vibe-deutsch bash

# Database inspection
sudo docker-compose exec vibe-deutsch python scripts/checks/inspect_database.py

# Resource usage
sudo docker stats vibe-deutsch
```

### Getting Help
1. Check Container Manager logs
2. Review application health check status
3. Test API endpoints at `http://nas-ip:8000/docs`
4. Verify environment variables in container

---

🎉 **Success!** Your Vibe Deutsch platform should now be running at `http://your-nas-ip:8000`