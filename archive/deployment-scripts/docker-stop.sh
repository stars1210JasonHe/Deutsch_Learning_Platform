#!/bin/bash

# Vibe Deutsch - Stop Container Script

CONTAINER_NAME="vibe-deutsch"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Stopping Vibe Deutsch container...${NC}"

# Stop container
docker stop $CONTAINER_NAME

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container stopped successfully!${NC}"
else
    echo -e "${RED}❌ Failed to stop container or container not running${NC}"
fi

# Optionally remove container (uncomment if needed)
echo -e "${YELLOW}🗑️ Removing container...${NC}"
docker rm $CONTAINER_NAME 2>/dev/null || true

echo -e "${GREEN}✅ Container stopped and removed${NC}"
echo -e "${YELLOW}💡 To restart: ./docker-run.sh${NC}"