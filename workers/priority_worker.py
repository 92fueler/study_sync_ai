#!/usr/bin/env python
"""
Priority Worker - processes priority recalculation and clustering jobs.

Listens to: low queue (batch operations)
Jobs: recalculate_priority, cluster_topics

Usage:
    python -m workers.priority_worker
"""

import os
from redis import Redis
from rq import Worker, Queue
from dotenv import load_dotenv

load_dotenv()


def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    conn = Redis.from_url(redis_url)
    
    # Priority recalc is batch/maintenance
    queues = [Queue("low", connection=conn)]
    
    worker = Worker(queues, connection=conn, name="priority-worker")
    
    print(f"Starting priority worker, listening to: low")
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
