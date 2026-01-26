#!/usr/bin/env python
"""
Notification Worker - processes notification jobs.

Listens to: low queue (notifications are low priority)
Jobs: send_notification, send_push_notification, send_email_notification

Usage:
    python -m workers.notification_worker
"""

import os
from redis import Redis
from rq import Worker, Queue
from dotenv import load_dotenv

load_dotenv()


def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    conn = Redis.from_url(redis_url)
    
    # Notifications are low priority
    queues = [Queue("low", connection=conn)]
    
    worker = Worker(queues, connection=conn, name="notification-worker")
    
    print(f"Starting notification worker, listening to: low")
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
