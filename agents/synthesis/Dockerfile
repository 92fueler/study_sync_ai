FROM python:3.13-slim

WORKDIR /app

COPY agents/synthesis/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/synthesis/ ./synthesis_agent/

EXPOSE 8003

CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8003", "."]
