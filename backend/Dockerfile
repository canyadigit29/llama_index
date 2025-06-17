# Use an official Python runtime as a parent image
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY README.md ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -e .

COPY . .
COPY backend/main.py ./

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
