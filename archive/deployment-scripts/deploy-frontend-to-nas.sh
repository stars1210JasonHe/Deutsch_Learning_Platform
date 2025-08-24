#!/bin/bash

# Configuration
NAS_IP="your-nas-ip"
NAS_USER="root"
NAS_PATH="/volume1/docker/LanguageLearning"

echo "Building frontend for production..."
cd frontend
npm run build
cd ..

echo "Creating deployment package..."
mkdir -p deploy-temp
cp -r frontend/dist deploy-temp/
cp Dockerfile.frontend deploy-temp/Dockerfile
cp nginx.conf deploy-temp/
cp docker-compose.frontend.yml deploy-temp/docker-compose.yml

echo "Uploading to NAS..."
scp -r deploy-temp/* ${NAS_USER}@${NAS_IP}:${NAS_PATH}/

echo "Connecting to NAS and deploying..."
ssh ${NAS_USER}@${NAS_IP} << EOF
cd ${NAS_PATH}
docker-compose down
docker-compose build
docker-compose up -d
echo "Frontend deployed successfully!"
EOF

echo "Cleaning up..."
rm -rf deploy-temp

echo "Deployment complete! Frontend should be available at http://${NAS_IP}"