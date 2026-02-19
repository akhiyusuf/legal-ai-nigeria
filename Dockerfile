# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables for non-interactive installs and CPU-only torch
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements and .env.example
COPY requirements.txt .

# Install EVERYTHING in one layer to minimize layers and image size
# 1. System deps needed for build & run
# 2. CPU-only torch
# 3. App requirements
# 4. Cleanup build-only deps and apt cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev && \
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential git && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of the application
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start command
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# Start command (Railway will override PORT if set, but we use the env var)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
