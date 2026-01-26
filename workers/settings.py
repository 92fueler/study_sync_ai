"""
RQ Worker settings and configuration.

This module provides settings for RQ workers.
Usage: rq worker --config workers.settings high default low
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Queue names in priority order
QUEUES = ["high", "default", "low"]

# Job timeout defaults
DEFAULT_RESULT_TTL = 500  # 500 seconds
DEFAULT_WORKER_TTL = 420  # 7 minutes

# Retry configuration
MAX_FAILURES = 3
