FROM python:3.13-slim

WORKDIR /app

COPY agents/profile/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/profile/ ./profile_agent/

EXPOSE 8002

CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8002", "."]
