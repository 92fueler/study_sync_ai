FROM python:3.13-slim

WORKDIR /app

COPY agents/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/orchestrator/ ./orchestrator/

EXPOSE 8005

CMD ["adk", "api_server", "--port", "8005", "orchestrator"]
