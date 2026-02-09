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
    """Build Gemini system instruction from Style DNA.
    
    Args:
        style_dna: Dictionary containing:
            - tone: Cognitive tone (textbook, coaching, beginner_friendly, key_points)
            - format_pref: Format preference (outline, cornell, mindmap)
            - uses_emoji: Whether to use emojis
            - prefers_diagrams: Whether to include diagrams
            - learning_preferences: List of preferences (analogies, real_world, concept_map, practice_set)
            - custom_style: User's custom style description
    
    Returns:
        Formatted system instruction string for Gemini
    """
    tone = style_dna.get("tone", "textbook")
    format_pref = style_dna.get("format_pref", "outline")
    uses_emoji = style_dna.get("uses_emoji", False)
    prefers_diagrams = style_dna.get("prefers_diagrams", True)
    learning_preferences = style_dna.get("learning_preferences", [])
    custom_style = style_dna.get("custom_style", "")
    
    tone_map = {
        "textbook": """Use clear, authoritative academic tone with precision and formality. Use:
- Technical terminology with proper definitions
- Structured explanations with logical flow
- Formal language appropriate for higher education
- Evidence-based statements
Example: "Neural networks employ backpropagation algorithms to minimize loss functions through gradient descent optimization." """,
        
        "coaching": """Use encouraging, motivational tone with warmth and support. Use:
- Positive, uplifting language
- "You can do this" and "Let's explore together" patterns
- Celebrate progress and understanding
- Guide with enthusiasm and patience
Example: "Great! Now let's dive into how neural networks learn. Think of it as training a team - each iteration makes them better at their job!" """,
        
        "beginner_friendly": """Use friendly, reassuring tone for first-time learners. Use:
- Simple, accessible language (avoid jargon unless necessary, then explain it)
- Analogies and everyday examples
- Step-by-step breakdowns
- Patient, welcoming approach
Example: "Neural networks are like a team of experts. Each expert (neuron) looks at part of the problem, and they vote on the answer." """,
        
        "key_points": """Use direct, efficient tone focused on essential information. Use:
- Concise, to-the-point explanations
- Bullet points and lists
- Skip elaboration unless critical
- Focus on actionable insights
Example: "Neural networks: layers of neurons → forward pass → calculate loss → backpropagation → update weights." """
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

TONE: {tone_map.get(tone, tone_map['textbook'])}

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
        style_dna: User's style preferences (includes tone, format_pref, uses_emoji, prefers_diagrams, learning_preferences, custom_style)
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
        
        # Auto-generate audio if user has 'audio' in their formats preference
        formats = style_dna.get("formats", [])
        if "audio" in formats:
            logger.info(f"Auto-generating audio for artifact {artifact_id} (user has 'audio' in formats)")
            try:
                # Import here to avoid circular dependency
                from .audio import generate_audio_from_text
                
                # Get cognitive tone for voice selection
                cognitive_tone = style_dna.get("tone", "textbook")
                
                # Generate audio asynchronously (don't wait for it)
                asyncio.create_task(
                    generate_audio_from_text(
                        text=full_content,
                        artifact_id=artifact_id,
                        cognitive_tone=cognitive_tone
                    )
                )
                logger.info(f"Audio generation task created for artifact {artifact_id}")
            except Exception as audio_error:
                # Don't fail the whole request if audio generation fails
                logger.warning(f"Audio generation failed for artifact {artifact_id}: {audio_error}")
        
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
        style_dna: User's style preferences (includes learning_preferences and custom_style)
    
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


async def _generate_script_async(content: str, topic: str, acts: List[Dict]) -> List[str]:
    """
    Generate a cinematic script for the video segments using Gemini.
    """
    client = _get_genai_client()
    if not client:
        return []
        
    total_segments = sum(act['segments'] for act in acts)
    
    # Build prompt structure
    structure_desc = []
    for act in acts:
        structure_desc.append(f"- Act {act['act']} ({act['style']}): {act['segments']} segments. "
                              f"Visual Style: {act['veo_mode']['visual_style']}")
    
    structure_text = "\\n".join(structure_desc)
    
    prompt = f"""You are an award-winning cinematic director for an educational video series.
    
Topic: {topic}
Source Material:
{content[:3000]}

Video Structure:
{structure_text}

Task:
Write a visual narrative script for the {total_segments} video segments.
Each segment is 8 seconds long.
The narrative should be purely VISUAL and ACTION-based descriptions for a video generation model.
Do not include camera angles or lighting (those are handled elsewhere).
Focus on the objects, motion, and transition of ideas.

Output Requirement:
Return ONLY a raw JSON list of strings.
Example: ["A red ball drops...", "The ball turns into a planet...", "Map zooms out..."]
Length: Exactly {total_segments} strings.
"""

    try:
        # Use sync call in thread pool if needed, or async if client supports it.
        # Here we assume client.aio is available or use run_async wrapper if sync.
        # Simpler: use the synchronous client inside _run_async wrapper if needed, 
        # but here we can just use the tool's pattern.
        # Actually tools.py uses _run_async for other things. 
        # But here we are already inside an async function.
        # Let's use the sync method wrapped in _run_async to be safe with this client setup.
        
        response = _run_async(lambda: client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        ))
        
        script = json.loads(response.text)
        if isinstance(script, list) and len(script) > 0:
            logger.info(f"Generated script with {len(script)} segments")
            return script
        else:
            logger.warning("Gemini returned invalid script format")
            return []
            
    except Exception as e:
        logger.error(f"Gemini script generation failed: {e}")
        return []


def generate_video(
    artifact_id: str,
    user_id: str,
    total_duration: int = 300  # Default to 5 minutes for full depth
) -> Dict[str, Any]:
    """
    Generate educational video for an artifact using Veo 3.
    
    Args:
        artifact_id: Artifact to generate video for
        user_id: User identifier
        total_duration: Total video duration in seconds (default 120 = 2 min)
    
    Returns:
        Dict with status and video generation job details
    """
    logger.info(f"generate_video called for artifact {artifact_id}")
    return _run_async(_generate_video_async(artifact_id, user_id, total_duration))


async def _generate_video_async(artifact_id: str, user_id: str, total_duration: int):
    conn = await _get_db_connection()
    try:
        # 1. Get artifact content
        artifact = await conn.fetchrow(
            "SELECT content, artifact_type FROM artifacts WHERE id = $1",
            artifact_id
        )
        if not artifact:
            return {"status": "error", "error": "Artifact not found"}
        
        # 2. Get user's learning preferences
        profile = await conn.fetchrow(
            "SELECT style_dna FROM user_profiles WHERE user_id = $1",
            user_id
        )
        
        style_dna = profile['style_dna'] if profile else {}
        if isinstance(style_dna, str):
            try:
                style_dna = json.loads(style_dna)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse style_dna for user {user_id}, using defaults")
                style_dna = {}

        user_prefs = style_dna.get('styles', ['real_world', 'concept_map'])
        cognitive_tone = style_dna.get('cognitive_tone', 'textbook')
        
        # 3. Categorize topic
        content = artifact['content'] or ""
        topic = f"Study material - {artifact['artifact_type']}"
        topic_category = categorize_topic(topic, content[:500])
        
        # 4. Sequence acts using Style Sequencer
        acts = sequence_video_acts(user_prefs, total_duration)
        
        logger.info(f"Sequenced {len(acts)} acts for video", extra={
            "artifact_id": artifact_id,
            "acts": [act['style'] for act in acts]
        })
        
        # 5. Create video_artifact record
        video_id = await conn.fetchval(
            """
            INSERT INTO video_artifacts (
                artifact_id, video_path, duration_seconds, file_size_bytes,
                resolution, aspect_ratio, prompt, topic_category,
                learning_style, cognitive_tone, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
            """,
            artifact_id,
            f"storage/video/{artifact_id}_complete.mp4",  # Final stitched video
            total_duration,
            0,  # Will be updated when complete
            "720p",
            "16:9",
            f"Educational video for {topic}",
            topic_category.value,
            ",".join([act['style'] for act in acts]),
            cognitive_tone,
            "generating"
        )
        
        # 6. Generate Script using Gemini (The "Director")
        try:
            script_narratives = await _generate_script_async(content, topic, acts)
        except Exception as e:
            logger.error(f"Script generation failed, using fallbacks: {e}")
            script_narratives = []
        
        # 7. Create segment records with optimized prompts
        segment_global_index = 0
        for act in acts:
            for i in range(act['segments']):
                # Get narrative from script or fallback
                if segment_global_index < len(script_narratives):
                    narrative = script_narratives[segment_global_index]
                else:
                    narrative = f"Segment {i+1} of {act['segments']}: Exploring {topic} through {act['style']} perspective"
                
                # Build optimized prompt using Triad Formula
                prompt = build_optimized_prompt(
                    topic=topic,
                    narrative=narrative,
                    user_style=act['style'],
                    cognitive_tone=cognitive_tone,
                    topic_category=topic_category,
                    base_veo_mode=act['veo_mode']
                )
                
                await conn.execute(
                    """
                    INSERT INTO video_segments (
                        video_artifact_id, segment_index, act_number, act_style,
                        segment_path, duration_seconds, file_size_bytes,
                        prompt, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    video_id,
                    segment_global_index,
                    act['act'],
                    act['style'],
                    f"storage/video/{artifact_id}_seg_{segment_global_index}.mp4",
                    8,
                    0,
                    prompt,
                    "pending"
                )
                segment_global_index += 1
        
        logger.info(f"Created video generation job with {segment_index} segments", extra={
            "video_id": str(video_id),
            "artifact_id": artifact_id
        })
        
        return {
            "status": "success",
            "video_id": str(video_id),
            "segments": segment_index,
            "total_duration": total_duration,
            "message": "Video generation started. Segments will be processed by video worker."
        }
        
    except Exception as e:
        logger.exception("generate_video failed", extra={"artifact_id": artifact_id})
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()

