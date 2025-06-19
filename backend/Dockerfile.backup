# Use an official Python runtime as a parent image
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY README.md ./
RUN pip install --no-cache-dir -e .
RUN pip install uvicorn
RUN pip install fastapi
RUN pip install python-multipart

COPY . .
COPY backend/main.py ./
COPY _llama-index/llama_index ./llama_index
COPY llama-index-integrations/vector_stores ./llama_index/vector_stores

EXPOSE 8000

# Create port fix scripts
RUN echo '#!/bin/bash\n\
echo "=== PORT CONFIGURATION CHECK ==="\n\
echo "PORT environment variable: $PORT"\n\
echo "Forcing PORT to 8000..."\n\
export PORT=8000\n\
echo "Starting application on port 8000"\n\
exec uvicorn main:app --host 0.0.0.0 --port 8000\n\
' > /app/entrypoint.sh

# Make it executable
RUN chmod +x /app/entrypoint.sh

# Use our entrypoint script to ensure we use port 8000
CMD ["/app/entrypoint.sh"]
