FROM python:3.13-slim

WORKDIR /app

COPY agents/ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ingestion/ ./ingestion_agent/

EXPOSE 8001

CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8001", "."]
