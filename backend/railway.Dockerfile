FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create data directory for temp storage
RUN mkdir -p data

# Copy application code
COPY main.py .
COPY Procfile .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose the port - explicitly use 8000 to match Railway's routing
EXPOSE 8000

# Use explicit port 8000 in the command to ensure consistency
CMD uvicorn main:app --host 0.0.0.0 --port 8000
