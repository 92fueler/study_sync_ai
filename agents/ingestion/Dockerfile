FROM python:3.13-slim

WORKDIR /app

COPY agents/ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ingestion/ ./ingestion/

EXPOSE 8001

CMD ["adk", "api_server", "--port", "8001", "ingestion"]
