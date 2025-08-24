# Manual Frontend Deployment to NAS

## Option 1: Docker Container (Recommended)

### Step 1: Create Frontend Directory
```bash
ssh root@your-nas-ip
mkdir -p /volume1/docker/Deutsch_Learning_Platform_Frontend
cd /volume1/docker/Deutsch_Learning_Platform_Frontend
```

### Step 2: Copy Frontend Files
```bash
# From Windows, copy frontend folder
scp -r E:/LanguageLearning/frontend/ root@your-nas-ip:/volume1/docker/Deutsch_Learning_Platform_Frontend/
```

### Step 3: Create Frontend Dockerfile
```bash
# On NAS
cat > Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ ./

# Build for production
RUN npm run build

# Install serve to serve static files
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Serve the built app
CMD ["serve", "-s", "dist", "-l", "3000"]
EOF
```

### Step 4: Create Docker Compose
```bash
# On NAS
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  frontend:
    build: .
    container_name: vibe-deutsch-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://your-nas-ip:8000
    networks:
      - frontend-network

networks:
  frontend-network:
    driver: bridge
EOF
```

### Step 5: Deploy
```bash
# On NAS
docker-compose up -d --build
```

## Option 2: Direct Node.js (Alternative)

### Step 1: Install Node.js on NAS
```bash
# Install via Package Center or manually
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install node
```

### Step 2: Copy and Run
```bash
cd /volume1/docker/Deutsch_Learning_Platform_Frontend/frontend
npm install
npm run build

# Install and run serve
npm install -g serve
serve -s dist -l 3000 &
```

## Verification

After deployment, check:
- Frontend: `http://your-nas-ip:3000`
- Backend: `http://your-nas-ip:8000`
- Logs: `docker-compose logs -f frontend`

## Environment Configuration

Make sure your frontend `.env` or `vite.config.ts` points to your NAS backend:
```
VITE_API_BASE_URL=http://your-nas-ip:8000
```