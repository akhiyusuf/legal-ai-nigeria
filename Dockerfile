# --- Build Stage ---
FROM python:3.11-slim as builder

# Install system build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and model download script
COPY requirements.txt .
COPY scripts/download_models.py scripts/

# Install dependencies and pre-download models
RUN pip install --no-cache-dir --user -r requirements.txt && \
    python scripts/download_models.py

# --- Runtime Stage ---
FROM python:3.11-slim

# Install ONLY runtime system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy the rest of the application (respecting .dockerignore)
COPY . .

# Set environment variable to store models in a persistent way
ENV SENTENCE_TRANSFORMERS_HOME=/root/.cache/torch/sentence_transformers
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/hub

# Expose the FastAPI port
EXPOSE 8000

# Start command
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# Start command (Railway will override PORT if set, but we use the env var)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
