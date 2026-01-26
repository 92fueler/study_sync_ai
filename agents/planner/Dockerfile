FROM python:3.13-slim

WORKDIR /app

COPY agents/planner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/planner/ ./planner/

EXPOSE 8004

CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8004", "."]
