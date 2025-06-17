# Use an official Python runtime as a parent image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pinecone-client>=3.0.2 && \
    pip install --no-cache-dir -r requirements.txt

# Create data directory for temp storage
RUN mkdir -p data

# Copy application code from backend directory
COPY backend .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose the port (Railway will override this)
EXPOSE ${PORT}

# Make startup script executable
RUN chmod +x start.sh

# Use the startup script to handle environment variables
CMD ["./start.sh"]
