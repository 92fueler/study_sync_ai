"""
Synthesis Agent Tools

ADK tools for generating personalized learning artifacts.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional

import asyncpg
from google import genai

# Import video generation modules
from .video_sequencer import sequence_video_acts, build_veo_prompt, build_transition_prompt
from .prompt_optimizer import categorize_topic, build_optimized_prompt

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=os.getenv("AGENT_LOG_LEVEL", "INFO"))

# ... (rest of existing code remains the same)
