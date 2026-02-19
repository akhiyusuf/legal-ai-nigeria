# Use official Python 3.11 slim image
FROM python:3.11-slim

# Install ONLY runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy exact local requirements
COPY requirements.txt .

# Install dependencies (matching local 690MB venv)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start command
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# Start command (Railway will override PORT if set, but we use the env var)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
