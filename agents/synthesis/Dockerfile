FROM python:3.13-slim

WORKDIR /app

COPY agents/synthesis/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/synthesis/ ./synthesis/

EXPOSE 8003

CMD ["adk", "api_server", "--port", "8003", "synthesis"]
