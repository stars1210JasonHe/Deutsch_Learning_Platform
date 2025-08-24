@echo off
REM Set your NAS IP
set NAS_IP=your-nas-ip

echo Building frontend...
cd frontend
npm run build
cd ..

echo Copying to NAS...
scp -r frontend/dist/* root@%NAS_IP%:/volume1/docker/Frontend/

echo Done! Now run these commands on your NAS:
echo cd /volume1/docker/Frontend
echo docker build -t frontend .
echo docker run -d -p 80:80 frontend