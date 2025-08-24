@echo off
REM Quick Frontend Deployment to NAS (Windows Batch)
REM Run this from E:\LanguageLearning\ directory

echo === Quick Frontend NAS Deployment ===
echo.

REM Configure these variables
set NAS_IP=your-nas-ip
set NAS_USER=root

echo Step 1: Creating frontend directory on NAS...
ssh %NAS_USER%@%NAS_IP% "mkdir -p /volume1/docker/Frontend"

echo Step 2: Copying frontend files...
scp -r frontend/ %NAS_USER%@%NAS_IP%:/volume1/docker/Frontend/

echo Step 3: Creating production Dockerfile...
ssh %NAS_USER%@%NAS_IP% "cat > /volume1/docker/Frontend/Dockerfile << 'EOF'
FROM node:18-alpine
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
RUN npm install -g serve
EXPOSE 3000
CMD [\"serve\", \"-s\", \"dist\", \"-l\", \"3000\"]
EOF"

echo Step 4: Creating docker-compose...
ssh %NAS_USER%@%NAS_IP% "cat > /volume1/docker/Frontend/docker-compose.yml << 'EOF'
version: '3.8'
services:
  frontend:
    build: .
    container_name: frontend-app
    restart: unless-stopped
    ports:
      - \"3000:3000\"
    environment:
      - VITE_API_BASE_URL=http://%NAS_IP%:8000
EOF"

echo Step 5: Building and starting...
ssh %NAS_USER%@%NAS_IP% "cd /volume1/docker/Frontend && docker-compose up -d --build"

echo.
echo === Deployment Complete ===
echo Frontend: http://%NAS_IP%:3000
echo Backend:  http://%NAS_IP%:8000
echo.
echo To check logs: ssh %NAS_USER%@%NAS_IP% "cd /volume1/docker/Frontend && docker-compose logs -f"
pause