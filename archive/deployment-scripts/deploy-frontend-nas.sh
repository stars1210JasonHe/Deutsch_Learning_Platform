#!/bin/bash
# Deploy Frontend to NAS Script
# This script sets up the frontend to run on your NAS

echo "=== Frontend NAS Deployment Script ==="

# Configuration
NAS_IP="your-nas-ip"  # Replace with your actual NAS IP
NAS_USER="root"
FRONTEND_DIR="/volume1/docker/Deutsch_Learning_Platform_Frontend"
BACKEND_URL="http://localhost:8000"  # Backend API URL

echo "1. Creating frontend directory on NAS..."
ssh $NAS_USER@$NAS_IP "mkdir -p $FRONTEND_DIR"

echo "2. Copying frontend files to NAS..."
scp -r frontend/ $NAS_USER@$NAS_IP:$FRONTEND_DIR/

echo "3. Creating frontend Dockerfile on NAS..."
ssh $NAS_USER@$NAS_IP "cat > $FRONTEND_DIR/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY frontend/ ./

# Expose port
EXPOSE 3000

# Start development server
CMD [\"npm\", \"run\", \"dev\", \"--\", \"--host\", \"0.0.0.0\"]
EOF"

echo "4. Creating docker-compose for frontend..."
ssh $NAS_USER@$NAS_IP "cat > $FRONTEND_DIR/docker-compose.yml << 'EOF'
version: '3.8'

services:
  frontend:
    build: .
    container_name: vibe-deutsch-frontend
    restart: unless-stopped
    ports:
      - \"3000:3000\"
    environment:
      - VITE_API_BASE_URL=http://$NAS_IP:8000
    volumes:
      - ./frontend:/app
    networks:
      - frontend-network

networks:
  frontend-network:
    driver: bridge
EOF"

echo "5. Building and starting frontend container..."
ssh $NAS_USER@$NAS_IP "cd $FRONTEND_DIR && docker-compose up -d --build"

echo "=== Deployment Complete ==="
echo "Frontend should be accessible at: http://$NAS_IP:3000"
echo "Backend API accessible at: http://$NAS_IP:8000"
echo ""
echo "To check frontend logs: ssh $NAS_USER@$NAS_IP 'cd $FRONTEND_DIR && docker-compose logs -f'"
echo "To stop frontend: ssh $NAS_USER@$NAS_IP 'cd $FRONTEND_DIR && docker-compose down'"