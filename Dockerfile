# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Add cache-busting argument 
ARG CACHE_BUST=12

WORKDIR /app

# Install system dependencies including Tesseract OCR and poppler-utils for PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    tesseract-ocr \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    # Install pinecone-client explicitly first to ensure correct version
    pip install --root-user-action=ignore --no-cache-dir pinecone-client>=3.0.2 && \
    # Install llama-index packages in the correct order
    pip install --root-user-action=ignore --no-cache-dir \
        llama-index-core>=0.10.27 \
        llama-index-vector-stores-pinecone>=0.1.6 \
        llama-index-embeddings-openai>=0.1.5 && \
    # Install the rest of requirements
    pip install --root-user-action=ignore --no-cache-dir -r requirements.txt && \
    # Install both PDF libraries to ensure at least one works
    pip install --no-cache-dir pypdf PyPDF2

# Create data directory for temp storage
RUN mkdir -p data

# Copy test_imports.py to root directory
COPY test_imports.py /app/

# Copy vector_store_config.py to root directory for better import compatibility
COPY vector_store_config.py /app/

# Copy application code from backend directory
COPY backend/ ./

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose port 8000 explicitly - this is what Railway expects
EXPOSE 8000

# Copy additional diagnostic files
COPY railway_deploy.sh /app/
COPY railway_troubleshoot.py /app/
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
