# Use official Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies (build-essential, git, poppler, tesseract)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and .env.example
COPY requirements.txt .

# Install dependencies (CPU-only torch first to save space)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start command
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# Start command (Railway will override PORT if set, but we use the env var)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
