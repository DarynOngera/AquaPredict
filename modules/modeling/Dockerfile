FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create model directories
RUN mkdir -p /app/models/trained /app/models/checkpoints

# Set environment variables
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
