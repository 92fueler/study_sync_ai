FROM python:3.13-slim

WORKDIR /app

# Install system dependencies used by video worker (stitching/placeholder generation)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY workers/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY workers/ ./workers/

# Default: run generation worker (can override in docker-compose)
CMD ["python", "-m", "workers.generation_worker"]
