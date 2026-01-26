FROM python:3.13-slim

WORKDIR /app

COPY agents/ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ingestion/ ./ingestion/

EXPOSE 8001

# Set PYTHONPATH so Python can find the ingestion module
ENV PYTHONPATH=/app

CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8001", "."]
