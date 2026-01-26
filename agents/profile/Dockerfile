FROM python:3.13-slim

WORKDIR /app

COPY agents/profile/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/profile/ ./profile/

EXPOSE 8002

CMD ["adk", "api_server", "--port", "8002", "profile"]
