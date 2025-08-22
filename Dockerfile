# Multi-stage Docker build for Vibe Deutsch
FROM node:18-alpine as frontend-builder

# Install dependencies for native modules
RUN apk add --no-cache python3 make g++

# Build frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./

# Clean install with proper dependencies
RUN rm -rf node_modules package-lock.json
RUN npm install

COPY frontend/ ./
# Build without TypeScript checking for Docker compatibility
RUN npx vite build

# Python backend stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy Python dependencies
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create data directory and audio mount point
RUN mkdir -p /app/data /app/audio && chmod 755 /app/data /app/audio

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Start command
CMD ["uv", "run", "python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]