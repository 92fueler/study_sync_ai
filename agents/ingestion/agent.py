"""
Ingestion Agent - Google ADK Implementation

Parses uploaded content, extracts topics, and generates embeddings.
"""

from google.adk.agents import LlmAgent
from .tools import ingest_content, extract_topics, generate_embedding

# Root agent exported for ADK
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="ingestion_agent",
    description="Parses uploaded content, extracts topics, and generates embeddings for StudySync AI",
    instruction="""You are the Ingestion Agent for StudySync AI. Your role is to:
1. Process uploaded content (text, PDFs, etc.)
2. Extract key topics from the content
3. Generate embeddings for semantic search

When a user uploads content:
- Use ingest_content to process and store the content
- The tool will automatically extract topics and generate embeddings
- Return the content_id and processing status

For topic extraction requests:
- Use extract_topics to analyze text and identify key themes

For embedding requests:
- Use generate_embedding to create vector representations

Always provide helpful status updates about processing progress.""",
    tools=[ingest_content, extract_topics, generate_embedding],
)
