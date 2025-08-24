#!/bin/bash

# Vibe Deutsch - Synology Safe Deployment Script
# Removes resource limits that cause issues on Synology NAS

# Configuration
CONTAINER_NAME="vibe-deutsch"
HOST_PORT="9876"  # Change this to your preferred port
IMAGE_NAME="vibe-deutsch:latest"
PROJECT_DIR="/volume1/docker/vibe-deutsch"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Vibe Deutsch Deployment Script (Synology Safe)${NC}"
echo -e "${YELLOW}Port: ${HOST_PORT}${NC}"
echo -e "${YELLOW}Container: ${CONTAINER_NAME}${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please copy .env.example to .env and configure your API keys${NC}"
    exit 1
fi

# Stop and remove existing container
echo -e "${YELLOW}🛑 Stopping existing container...${NC}"
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Build the image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p ${PROJECT_DIR}/data

# Run the container (WITHOUT resource limits for Synology compatibility)
echo -e "${YELLOW}🚀 Starting container...${NC}"
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p ${HOST_PORT}:8000 \
  -v ${PROJECT_DIR}/data:/app/data \
  -v ${PROJECT_DIR}/.env:/app/.env:ro \
  --env-file .env \
  $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container started successfully!${NC}"
    echo -e "${GREEN}🌐 Backend API: http://$(hostname -I | awk '{print $1}'):${HOST_PORT}${NC}"
    echo -e "${GREEN}📚 API Docs: http://$(hostname -I | awk '{print $1}'):${HOST_PORT}/docs${NC}"
    echo -e "${YELLOW}⚠️  Note: This deploys BACKEND ONLY. Frontend needs separate deployment.${NC}"
    echo -e "${YELLOW}📊 Check status: docker ps${NC}"
    echo -e "${YELLOW}📝 View logs: docker logs $CONTAINER_NAME${NC}"
else
    echo -e "${RED}❌ Failed to start container!${NC}"
    echo -e "${YELLOW}💡 Try removing resource limits if this fails${NC}"
    exit 1
fi