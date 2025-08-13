@echo off
echo Starting Vue 3 Frontend
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
    echo.
)

echo Starting development server...
echo Frontend will be available at: http://localhost:3000
echo.

npm run dev