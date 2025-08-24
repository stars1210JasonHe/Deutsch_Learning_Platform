#!/bin/bash

# Vibe Deutsch - Single Container Deployment Script
# For Synology NAS without docker-compose

# Configuration
CONTAINER_NAME="vibe-deutsch"
HOST_PORT="7777"  # Custom port for your app
IMAGE_NAME="vibe-deutsch:latest"
PROJECT_DIR="/volume1/docker/Deutsch_Learning_Platform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Vibe Deutsch Deployment Script${NC}"
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
mkdir -p ./data

# Run the container (Synology-safe without resource limits)
echo -e "${YELLOW}🚀 Starting container...${NC}"
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p ${HOST_PORT}:8000 \
  -v ${PWD}/data:/app/data \
  -v ${PWD}/.env:/app/.env:ro \
  --env-file .env \
  $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container started successfully!${NC}"
    echo -e "${GREEN}🌐 Access your app at: http://$(hostname -I | awk '{print $1}'):${HOST_PORT}${NC}"
    echo -e "${YELLOW}📊 Check status: docker ps${NC}"
    echo -e "${YELLOW}📝 View logs: docker logs $CONTAINER_NAME${NC}"
else
    echo -e "${RED}❌ Failed to start container!${NC}"
    exit 1
fi