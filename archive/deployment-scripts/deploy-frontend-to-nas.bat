@echo off
setlocal

REM Configuration - Update these values
set NAS_IP=your-nas-ip
set NAS_USER=root
set NAS_PATH=/volume1/docker/LanguageLearning

echo Building frontend for production...
cd frontend
call npm run build
cd ..

echo Creating deployment package...
if exist deploy-temp rmdir /s /q deploy-temp
mkdir deploy-temp
xcopy /E /I frontend\dist deploy-temp\dist\
copy Dockerfile.frontend deploy-temp\Dockerfile
copy nginx.conf deploy-temp\
copy docker-compose.frontend.yml deploy-temp\docker-compose.yml

echo.
echo Uploading to NAS...
echo Please run the following commands manually:
echo.
echo 1. Upload files to NAS:
echo    scp -r deploy-temp/* %NAS_USER%@%NAS_IP%:%NAS_PATH%/
echo.
echo 2. Connect to NAS and deploy:
echo    ssh %NAS_USER%@%NAS_IP%
echo    cd %NAS_PATH%
echo    docker-compose down
echo    docker-compose build
echo    docker-compose up -d
echo.
echo 3. Frontend will be available at: http://%NAS_IP%

pause