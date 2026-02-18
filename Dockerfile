# Use official Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies (Poppler and Tesseract for PDF handling)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the entire project first
COPY . .

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download the spaCy model explicitly
RUN python -m spacy download en_core_web_sm

# Expose the FastAPI port
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
