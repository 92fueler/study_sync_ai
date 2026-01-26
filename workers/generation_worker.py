#!/usr/bin/env python
"""
Generation Worker - processes artifact generation jobs.

Listens to: high, default queues
Jobs: generate_artifact, regenerate_artifact

Usage:
    python -m workers.generation_worker
    
Or via rq:
    rq worker --config workers.settings high default
"""

import os
import sys
from redis import Redis
from rq import Worker, Queue
from dotenv import load_dotenv

load_dotenv()


def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    conn = Redis.from_url(redis_url)
    
    # Listen to high and default queues (not low - that's for batch jobs)
    queues = [Queue("high", connection=conn), Queue("default", connection=conn)]
    
    worker = Worker(queues, connection=conn, name="generation-worker")
    
    print(f"Starting generation worker, listening to: high, default")
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
