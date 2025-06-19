# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Add cache-busting argument 
ARG CACHE_BUST=2

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --root-user-action=ignore --no-cache-dir pinecone>=3.0.2 && \
    pip install --root-user-action=ignore --no-cache-dir -r requirements.txt

# Create data directory for temp storage
RUN mkdir -p data

# Copy application code from backend directory
COPY backend/ ./

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose port 8000 explicitly - this is what Railway expects
EXPOSE 8000

# Copy additional diagnostic files
COPY railway_deploy.sh /app/
# These files are already copied from the backend directory, so we don't need to copy them again
# COPY backend/test_server.py /app/
# COPY backend/healthcheck.py /app/

# Make startup scripts executable
RUN chmod +x /app/start.sh || echo "Warning: start.sh not found"
RUN chmod +x /app/railway_deploy.sh || echo "Warning: railway_deploy.sh not found"

# List files for debugging
RUN ls -la /app/

# Use our comprehensive deployment script
CMD ["/app/railway_deploy.sh"]
