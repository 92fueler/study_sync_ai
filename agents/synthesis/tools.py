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

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=os.getenv("AGENT_LOG_LEVEL", "INFO"))

# Lazy-initialized Gemini client
_client = None


def _get_genai_client():
    """Get or create the Gemini client lazily."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            _client = genai.Client(api_key=api_key)
    return _client


async def _get_db_connection():
    dsn = os.getenv("SUPABASE_URL", "")
    logger.debug("Connecting to DB for synthesis tools")
    return await asyncpg.connect(dsn)


def _run_async(coro):
    """Run async coroutine safely, handling existing event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def _build_system_instruction(style_dna: Dict[str, Any]) -> str:
    """Build Gemini system instruction from Style DNA."""
    tone = style_dna.get("tone", "eli5")
    format_pref = style_dna.get("format_pref", "outline")
    uses_emoji = style_dna.get("uses_emoji", False)
    prefers_diagrams = style_dna.get("prefers_diagrams", True)
    
    tone_map = {
        "eli5": """Explain concepts simply, as if to a 10-year-old. Use:
- Analogies and everyday examples
- Simple language (avoid jargon unless necessary, then explain it)
- Step-by-step breakdowns
- "Imagine that..." scenarios
Example: "Neural networks are like a team of experts. Each expert (neuron) looks at part of the problem, and they vote on the answer." """,
        
        "socratic": """Use a questioning approach to guide understanding. Use:
- Thought-provoking questions that lead to insights
- "Why do you think...?" and "What if...?" patterns
- Progressive revelation (build understanding through questions)
- Encourage critical thinking
Example: "Why might a neural network need multiple layers? What happens if we only have one layer?" """,
        
        "academic": """Use formal, precise language appropriate for higher education. Use:
- Technical terminology with proper definitions
- Citations and references where relevant
- Structured arguments with evidence
- Domain-specific conventions
Example: "Neural networks employ backpropagation algorithms to minimize loss functions through gradient descent optimization." """
    }
    
    format_map = {
        "cornell": """Use Cornell note format with three sections:
1. CUE COLUMN (left): Key questions, terms, prompts
2. NOTES SECTION (right): Detailed explanations, examples, connections
3. SUMMARY (bottom): 2-3 sentence synthesis of main points

Structure each major concept as:
[CUE] → [NOTES] → [SUMMARY]""",
        
        "mindmap": """Organize content hierarchically with clear branches:
- Central topic at the root
- Main themes as primary branches
- Details as sub-branches
- Use visual hierarchy (indentation, bullets)
- Show connections between related concepts

Format:
# Central Topic
## Main Theme 1
  - Detail 1.1
  - Detail 1.2
## Main Theme 2
  - Detail 2.1""",
        
        "outline": """Use a clean outline format:
- Clear hierarchical headers (H1, H2, H3)
- Bullet points for lists
- Numbered lists for sequences/steps
- Consistent indentation
- Table of contents at the top"""
    }
    
    emoji_guidance = """Use emojis strategically to:
- Highlight key concepts (🎯 Main Point)
- Indicate sections (📚 Theory, 💡 Example, ⚠️ Warning)
- Make content scannable
- Enhance engagement without overuse
Limit: 1-2 emojis per major section""" if uses_emoji else "Do not use emojis. Keep content professional and text-focused."
    
    diagram_guidance = """Include Mermaid diagrams for:
- Complex processes (flowcharts)
- Relationships (entity-relationship diagrams)
- Hierarchies (tree structures)
- Sequences (sequence diagrams)

Format: Use ```mermaid code blocks. Keep diagrams simple and readable.
Example: ```mermaid
graph TD
    A[Input] --> B[Process]
    B --> C[Output]
```""" if prefers_diagrams else "Focus on text explanations. Avoid diagrams unless absolutely necessary for clarity."
    
    return f"""You are an expert study material synthesizer creating personalized learning content for StudySync AI.

YOUR MISSION:
Transform source material into clear, engaging, and effective study notes that match the user's learning preferences.

STYLE PREFERENCES:

TONE: {tone_map.get(tone, tone_map['eli5'])}

FORMAT: {format_map.get(format_pref, format_map['outline'])}

EMOJIS: {emoji_guidance}

DIAGRAMS: {diagram_guidance}

CONTENT QUALITY STANDARDS:
1. ACCURACY: Maintain factual accuracy from source material. Do not invent facts.
2. COMPLETENESS: Cover all major concepts from the source, prioritizing by importance
3. CLARITY: Explain complex ideas in accessible ways matching the chosen tone
4. STRUCTURE: Follow the specified format consistently throughout
5. ENGAGEMENT: Make content interesting and memorable (within tone constraints)
6. ACTIONABILITY: Include practical examples, applications, or exercises when relevant

OUTPUT STRUCTURE (for all formats):
1. OVERVIEW: 2-3 sentence summary of what will be covered
2. MAIN CONTENT: Organized according to format preference
3. KEY TAKEAWAYS: Bulleted list of 3-5 most important points
4. SUMMARY: Brief recap of main concepts
5. NEXT STEPS: Suggested follow-up topics or practice areas (if applicable)

COMMON PITFALLS TO AVOID:
- Don't copy source material verbatim (synthesize and rephrase)
- Don't oversimplify complex topics (maintain depth appropriate to tone)
- Don't skip important details (balance completeness with readability)
- Don't mix formats (stick to the chosen format consistently)
- Don't add information not in the source (maintain accuracy)

Remember: Your goal is to create study materials that help users learn effectively while matching their preferred style."""


def generate_artifact(
    user_id: str,
    content_ids: List[str],
    profile_version: int,
    style_dna: Dict[str, Any],
    time_available_minutes: int = 25
) -> Dict[str, Any]:
    """
    Generate a full personalized study artifact.
    
    Args:
        user_id: User identifier
        content_ids: List of source content IDs to synthesize
        profile_version: Profile version for cache key
        style_dna: User's style preferences (tone, format_pref, uses_emoji, prefers_diagrams)
        time_available_minutes: Target reading time
    
    Returns:
        Dict with status, artifact_id, content, content_5min, estimated_minutes
    """
    logger.info("generate_artifact called", extra={"user_id": user_id, "content_ids": len(content_ids), "minutes": time_available_minutes})
    return _run_async(
        _generate_artifact_async(user_id, content_ids, profile_version, style_dna, time_available_minutes)
    )


async def _generate_artifact_async(
    user_id: str,
    content_ids: List[str],
    profile_version: int,
    style_dna: Dict[str, Any],
    time_available_minutes: int
) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        # Check cache
        cached = await conn.fetchrow(
            """
            SELECT * FROM artifacts 
            WHERE user_id = $1 AND content_ids = $2 AND profile_version = $3 AND artifact_type = 'full'
            ORDER BY created_at DESC LIMIT 1
            """,
            user_id, content_ids, profile_version
        )
        
        if cached:
            result = {
                "status": "success",
                "artifact_id": str(cached["id"]),
                "content": cached["content"],
                "estimated_minutes": cached.get("estimated_minutes", time_available_minutes),
                "cached": True
            }
            logger.info("generate_artifact cache hit", extra={"user_id": user_id, "artifact_id": result["artifact_id"]})
            return result
        
        # Get source content
        source_texts = []
        for cid in content_ids:
            row = await conn.fetchrow("SELECT raw_text, title FROM content_items WHERE id = $1", cid)
            if row and row.get("raw_text"):
                source_texts.append(row["raw_text"])
        
        if not source_texts:
            logger.info("generate_artifact no source content", extra={"user_id": user_id})
            return {"status": "error", "error": "No source content found"}
        
        combined = "\n\n---\n\n".join(source_texts)
        system_instruction = _build_system_instruction(style_dna)
        
        # Generate full artifact
        target_words = time_available_minutes * 200
        full_prompt = f"""{system_instruction}

TASK: Create a comprehensive study note from the source material below.

CONTEXT:
- User has {time_available_minutes} minutes available for reading
- Target word count: approximately {target_words} words (assuming ~200 words/minute reading speed)
- Source material may contain multiple documents or sections

SOURCE MATERIAL:
{combined[:20000]}

GENERATION INSTRUCTIONS:

STEP 1: Analyze the source material
- Identify the main themes and concepts
- Note any dependencies or prerequisites
- Identify key examples, case studies, or applications
- Note any technical terms that need explanation

STEP 2: Structure your response
- Follow the format preference specified in your system instructions
- Organize content logically (foundational concepts first, then applications)
- Ensure smooth flow between sections
- Use clear transitions

STEP 3: Synthesize content
- Combine information from multiple sources if provided
- Resolve any contradictions (note if source material conflicts)
- Highlight connections between concepts
- Add context that helps understanding (within tone constraints)

STEP 4: Enhance for learning
- Include examples that illustrate concepts
- Add analogies if tone allows
- Create memory aids (mnemonics, patterns) where helpful
- Suggest practical applications

STEP 5: Finalize
- Ensure all key concepts are covered
- Verify format consistency
- Check that content matches tone preference
- Add summary and key takeaways

OUTPUT REQUIREMENTS:
- Start with a clear title/overview
- Follow the specified format (cornell/mindmap/outline)
- Include all sections specified in system instructions
- Maintain factual accuracy from source
- Target approximately {target_words} words
- End with key takeaways and summary

Generate the study note now:"""
        
        full_response = _get_genai_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )
        full_content = full_response.text
        
        # Generate 5-min version
        five_prompt = f"""{system_instruction}

TASK: Create a 5-minute quick summary (approximately 1000 words) focusing on the most essential information.

CONTEXT:
- User has limited time (5 minutes)
- This is a condensed version for quick review or preview
- Should capture the essence without deep detail

SOURCE MATERIAL:
{combined[:12000]}

SUMMARY STRATEGY:

PRIORITIZE:
1. Core concepts and definitions (what is it?)
2. Key principles or rules (how does it work?)
3. Main applications or use cases (why does it matter?)
4. Critical examples or case studies (concrete illustration)

OMIT:
- Detailed explanations (save for full version)
- Extended examples (keep to 1-2 brief examples)
- Background context (unless essential)
- Edge cases or exceptions (unless critical)

STRUCTURE:
1. ONE-SENTENCE OVERVIEW: What is this about?
2. KEY CONCEPTS: 3-5 main ideas with brief explanations
3. ESSENTIAL DETAILS: Critical information needed to understand
4. QUICK EXAMPLES: 1-2 brief, memorable examples
5. ACTION ITEMS: What should the user remember or do next?

OUTPUT REQUIREMENTS:
- Maximum 1000 words (target: 800-1000)
- Use the specified format preference (but simplified)
- Maintain tone preference
- Focus on actionable insights
- Make it scannable (use headers, bullets, bold)
- End with "Key Takeaways" section (3-5 bullet points)

Generate the 5-minute summary now:"""
        
        five_response = _get_genai_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=five_prompt
        )
        five_content = five_response.text
        
        # Estimate time
        word_count = len(full_content.split())
        estimated_minutes = max(1, word_count // 200)
        
        # Store full artifact
        row = await conn.fetchrow(
            """
            INSERT INTO artifacts (user_id, content_ids, profile_version, artifact_type, content, estimated_minutes)
            VALUES ($1, $2, $3, 'full', $4, $5)
            RETURNING id
            """,
            user_id, content_ids, profile_version, full_content, estimated_minutes
        )
        artifact_id = str(row["id"])
        
        # Store 5-min artifact
        await conn.execute(
            """
            INSERT INTO artifacts (user_id, content_ids, profile_version, artifact_type, content, estimated_minutes)
            VALUES ($1, $2, $3, '5min', $4, 5)
            """,
            user_id, content_ids, profile_version, five_content
        )
        
        result = {
            "status": "success",
            "artifact_id": artifact_id,
            "content": full_content,
            "content_5min": five_content,
            "estimated_minutes": estimated_minutes,
            "cached": False
        }
        logger.info("generate_artifact completed", extra={"user_id": user_id, "artifact_id": artifact_id})
        return result
    except Exception as e:
        logger.exception("generate_artifact failed", extra={"user_id": user_id})
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def generate_5min_summary(
    user_id: str,
    content_id: str,
    profile_version: int,
    style_dna: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate only a 5-minute summary.
    
    Args:
        user_id: User identifier
        content_id: Single content ID to summarize
        profile_version: Profile version for cache
        style_dna: User's style preferences
    
    Returns:
        Dict with status, artifact_id, content, estimated_minutes (always 5)
    """
    logger.info("generate_5min_summary called", extra={"user_id": user_id, "content_id": content_id})
    return _run_async(
        _generate_5min_async(user_id, content_id, profile_version, style_dna)
    )


async def _generate_5min_async(
    user_id: str,
    content_id: str,
    profile_version: int,
    style_dna: Dict[str, Any]
) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow("SELECT raw_text FROM content_items WHERE id = $1", content_id)
        if not row:
            logger.info("generate_5min_summary content not found", extra={"content_id": content_id})
            return {"status": "error", "error": "Content not found"}
        
        system_instruction = _build_system_instruction(style_dna)
        
        prompt = f"""{system_instruction}

TASK: Create a 5-minute quick summary (approximately 1000 words) focusing on the most essential information.

CONTEXT:
- User has limited time (5 minutes)
- This is a condensed version for quick review or preview
- Should capture the essence without deep detail

SOURCE MATERIAL:
{row['raw_text'][:12000]}

SUMMARY STRATEGY:

PRIORITIZE:
1. Core concepts and definitions (what is it?)
2. Key principles or rules (how does it work?)
3. Main applications or use cases (why does it matter?)
4. Critical examples or case studies (concrete illustration)

OMIT:
- Detailed explanations (save for full version)
- Extended examples (keep to 1-2 brief examples)
- Background context (unless essential)
- Edge cases or exceptions (unless critical)

STRUCTURE:
1. ONE-SENTENCE OVERVIEW: What is this about?
2. KEY CONCEPTS: 3-5 main ideas with brief explanations
3. ESSENTIAL DETAILS: Critical information needed to understand
4. QUICK EXAMPLES: 1-2 brief, memorable examples
5. ACTION ITEMS: What should the user remember or do next?

OUTPUT REQUIREMENTS:
- Maximum 1000 words (target: 800-1000)
- Use the specified format preference (but simplified)
- Maintain tone preference
- Focus on actionable insights
- Make it scannable (use headers, bullets, bold)
- End with "Key Takeaways" section (3-5 bullet points)

Generate the 5-minute summary now:"""
        
        response = _get_genai_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        artifact_row = await conn.fetchrow(
            """
            INSERT INTO artifacts (user_id, content_ids, profile_version, artifact_type, content, estimated_minutes)
            VALUES ($1, $2, $3, '5min', $4, 5)
            RETURNING id
            """,
            user_id, [content_id], profile_version, response.text
        )
        
        result = {
            "status": "success",
            "artifact_id": str(artifact_row["id"]),
            "content": response.text,
            "estimated_minutes": 5
        }
        logger.info("generate_5min_summary completed", extra={"user_id": user_id, "artifact_id": result["artifact_id"]})
        return result
    except Exception as e:
        logger.exception("generate_5min_summary failed", extra={"user_id": user_id})
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def get_artifact(artifact_id: str) -> Dict[str, Any]:
    """
    Get a specific artifact by ID.
    
    Args:
        artifact_id: The artifact UUID
    
    Returns:
        Dict with status and artifact details or error
    """
    logger.info("get_artifact called", extra={"artifact_id": artifact_id})
    return _run_async(_get_artifact_async(artifact_id))


async def _get_artifact_async(artifact_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM artifacts WHERE id = $1", artifact_id)
        if not row:
            logger.info("get_artifact not found", extra={"artifact_id": artifact_id})
            return {"status": "error", "error": "Artifact not found"}
        result = {
            "status": "success",
            "id": str(row["id"]),
            "content": row["content"],
            "artifact_type": row["artifact_type"],
            "estimated_minutes": row.get("estimated_minutes"),
            "created_at": str(row["created_at"])
        }
        logger.info("get_artifact completed", extra={"artifact_id": artifact_id})
        return result
    except Exception as e:
        logger.exception("get_artifact failed", extra={"artifact_id": artifact_id})
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def list_artifacts(user_id: str, artifact_type: Optional[str] = None) -> Dict[str, Any]:
    """
    List artifacts for a user.
    
    Args:
        user_id: User identifier
        artifact_type: Filter by type ('full', '5min', 'quiz') - optional
    
    Returns:
        Dict with status and list of artifact summaries
    """
    logger.info("list_artifacts called", extra={"user_id": user_id, "artifact_type": artifact_type})
    return _run_async(_list_artifacts_async(user_id, artifact_type))


async def _list_artifacts_async(user_id: str, artifact_type: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        if artifact_type:
            rows = await conn.fetch(
                "SELECT id, artifact_type, estimated_minutes, created_at FROM artifacts WHERE user_id = $1 AND artifact_type = $2 ORDER BY created_at DESC",
                user_id, artifact_type
            )
        else:
            rows = await conn.fetch(
                "SELECT id, artifact_type, estimated_minutes, created_at FROM artifacts WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
        result = {
            "status": "success",
            "artifacts": [
                {"id": str(r["id"]), "artifact_type": r["artifact_type"], "estimated_minutes": r.get("estimated_minutes"), "created_at": str(r["created_at"])}
                for r in rows
            ]
        }
        logger.info("list_artifacts completed", extra={"user_id": user_id, "count": len(result["artifacts"])})
        return result
    except Exception as e:
        logger.exception("list_artifacts failed", extra={"user_id": user_id})
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()
