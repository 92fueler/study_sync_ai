FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY workers/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY workers/ ./workers/

# Default: run generation worker (can override in docker-compose)
CMD ["python", "-m", "workers.generation_worker"]
