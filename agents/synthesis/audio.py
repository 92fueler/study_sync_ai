"""
Audio Generation Tools

Functions for converting text to speech using Gemini TTS API.
"""

import wave
import os
import logging
from typing import Dict, Any, Optional
from google.genai import types

# Import shared utilities from tools module
from .tools import _get_genai_client, _get_db_connection, _run_async

logger = logging.getLogger(__name__)


def _get_voice_for_tone(cognitive_tone: str) -> str:
    """
    Map cognitive tone to appropriate voice.
    
    Args:
        cognitive_tone: User's selected cognitive tone
    
    Returns:
        Voice name for Gemini TTS
    """
    voice_map = {
        "textbook": "Puck",      # Clear, authoritative
        "coaching": "Kore",      # Warm, encouraging
        "beginner_friendly": "Charon",  # Friendly, approachable
        "key_points": "Fenrir"   # Direct, efficient
    }
    return voice_map.get(cognitive_tone, "Kore")


def _get_style_prompt_for_tone(cognitive_tone: str) -> str:
    """
    Get TTS style prompt based on cognitive tone.
    
    Args:
        cognitive_tone: User's selected cognitive tone
    
    Returns:
        Style prompt to guide TTS generation
    """
    style_prompts = {
        "textbook": "Read this in a clear, authoritative academic tone. Speak with precision and formality, as if lecturing in a university.",
        
        "coaching": "Read this in an encouraging, motivational tone. Use a warm, supportive voice that guides the listener through the material with enthusiasm.",
        
        "beginner_friendly": "Read this in a friendly, reassuring tone. Speak slowly and clearly, as if explaining to someone learning for the first time. Be patient and welcoming.",
        
        "key_points": "Read this in a direct, efficient tone. Speak clearly and concisely, getting straight to the point without elaboration."
    }
    return style_prompts.get(cognitive_tone, "")


def _chunk_text(text: str, max_chars: int = 95000) -> list[str]:
    """
    Split text into chunks that fit within TTS API limits.
    Tries to split on sentence boundaries to maintain natural flow.
    
    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk (leave room for style prompt)
    
    Returns:
        List of text chunks
    """
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split on sentence boundaries (., !, ?, or newlines)
    import re
    sentences = re.split(r'([.!?\n]+\s*)', text)
    
    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        separator = sentences[i + 1] if i + 1 < len(sentences) else ""
        full_sentence = sentence + separator
        
        # If adding this sentence would exceed limit, save current chunk
        if len(current_chunk) + len(full_sentence) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = full_sentence
        else:
            current_chunk += full_sentence
    
    # Add the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    logger.info(f"Split text into {len(chunks)} chunks (original: {len(text)} chars)")
    return chunks


async def _combine_audio_segments(segments: list[bytes], output_path: str) -> None:
    """
    Combine multiple audio segments into a single WAV file.
    
    Args:
        segments: List of PCM audio data bytes
        output_path: Path to save combined audio
    """
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(24000)  # 24kHz
        
        # Write all segments
        for segment in segments:
            wf.writeframes(segment)
    
    logger.info(f"Combined {len(segments)} audio segments into {output_path}")


async def generate_audio_from_text(
    text: str,
    voice_name: str = "Kore",
    style_prompt: Optional[str] = None,
    artifact_id: Optional[str] = None,
    cognitive_tone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate audio from text using Gemini TTS API.
    
    Args:
        text: The text content to convert to speech
        voice_name: Voice to use (default: Kore)
        style_prompt: Optional prompt to control speech style
        artifact_id: Optional artifact ID to associate audio with
        cognitive_tone: Optional cognitive tone to auto-select voice and style
    
    Returns:
        Dict with status, audio_url, duration, file_size
    """
    try:
        # Auto-select voice and style based on cognitive tone
        if cognitive_tone:
            voice_name = _get_voice_for_tone(cognitive_tone)
            if not style_prompt:
                style_prompt = _get_style_prompt_for_tone(cognitive_tone)
        
        client = _get_genai_client()
        if not client:
            return {
                "status": "error",
                "error": "Gemini client not initialized. Check GEMINI_API_KEY."
            }
        
        # Check if text needs chunking (32k tokens ≈ 100k chars, leave 5k for style prompt)
        max_chars = 95000
        text_chunks = _chunk_text(text, max_chars)
        
        logger.info(f"Generating audio with voice={voice_name}, chunks={len(text_chunks)}, total_length={len(text)}")
        
        # Generate audio for each chunk
        audio_segments = []
        for i, chunk in enumerate(text_chunks):
            logger.info(f"Generating audio for chunk {i+1}/{len(text_chunks)} ({len(chunk)} chars)")
            
            # Build the prompt with style guidance
            if style_prompt:
                prompt = f"{style_prompt}\n\n{chunk}"
            else:
                prompt = chunk
            
            # Generate audio using Gemini TTS
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name
                            )
                        )
                    )
                )
            )
            
            # Extract audio data
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            audio_segments.append(audio_data)
            
            logger.info(f"Chunk {i+1} audio generated: {len(audio_data)} bytes")
        
        # Generate filename (use AUDIO_STORAGE_DIR in Docker so gateway and synthesis share same volume)
        audio_filename = f"{artifact_id or 'audio'}_{voice_name}.wav"
        audio_dir = os.getenv("AUDIO_STORAGE_DIR", "storage/audio")
        audio_path = os.path.join(audio_dir, audio_filename)
        
        # Ensure directory exists
        os.makedirs(audio_dir, exist_ok=True)
        
        # Combine audio segments into single file
        if len(audio_segments) == 1:
            # Single segment - just save it
            with wave.open(audio_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(audio_segments[0])
        else:
            # Multiple segments - combine them
            await _combine_audio_segments(audio_segments, audio_path)
        
        # Get file size
        file_size = os.path.getsize(audio_path)
        
        # Calculate duration (bytes / (sample_rate * sample_width * channels))
        # Sum of lengths of all audio segments
        total_audio_data_length = sum(len(s) for s in audio_segments)
        duration_seconds = total_audio_data_length / (24000 * 2 * 1)
        
        logger.info(f"Audio generated: {audio_filename}, duration={duration_seconds:.1f}s, size={file_size} bytes")
        
        # Store metadata in database
        conn = await _get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO audio_artifacts (artifact_id, audio_path, voice_name, duration_seconds, file_size_bytes)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (artifact_id) DO UPDATE SET
                    audio_path = $2,
                    voice_name = $3,
                    duration_seconds = $4,
                    file_size_bytes = $5,
                    generated_at = NOW()
                """,
                artifact_id, audio_path, voice_name, duration_seconds, file_size
            )
            
            # Update artifacts table with audio_url
            await conn.execute(
                """
                UPDATE artifacts
                SET audio_url = $1
                WHERE id = $2
                """,
                f"/api/v1/audio/{audio_filename}",
                artifact_id
            )
        finally:
            await conn.close()
        
        return {
            "status": "success",
            "audio_url": f"/api/v1/audio/{audio_filename}",
            "audio_path": audio_path,
            "duration_seconds": duration_seconds,
            "file_size_bytes": file_size,
            "voice_name": voice_name
        }
        
    except Exception as e:
        logger.exception("Audio generation failed")
        return {
            "status": "error",
            "error": str(e)
        }


def generate_audio(
    artifact_id: str,
    voice_name: str = "Kore",
    cognitive_tone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for generate_audio_from_text.
    Fetches artifact content and generates audio.
    
    Args:
        artifact_id: UUID of the artifact
        voice_name: Voice to use for TTS
        cognitive_tone: Optional cognitive tone for auto-selection
    
    Returns:
        Dict with status and audio metadata
    """
    return _run_async(_generate_audio_async(artifact_id, voice_name, cognitive_tone))


async def _generate_audio_async(
    artifact_id: str,
    voice_name: str,
    cognitive_tone: Optional[str]
) -> Dict[str, Any]:
    """
    Async implementation of generate_audio.
    """
    try:
        # Fetch artifact content from database (artifacts has content only, no title)
        conn = await _get_db_connection()
        try:
            row = await conn.fetchrow(
                """
                SELECT content
                FROM artifacts
                WHERE id = $1
                """,
                artifact_id
            )
            
            if not row:
                return {
                    "status": "error",
                    "error": f"Artifact {artifact_id} not found"
                }
            
            content = row['content']
            
        finally:
            await conn.close()
        
        # Generate audio
        result = await generate_audio_from_text(
            text=content,
            voice_name=voice_name,
            artifact_id=artifact_id,
            cognitive_tone=cognitive_tone
        )
        
        if result["status"] == "success":
            logger.info(f"Audio generated for artifact {artifact_id}: {result['audio_url']}")
        
        return result
        
    except Exception as e:
        logger.exception(f"Failed to generate audio for artifact {artifact_id}")
        return {
            "status": "error",
            "error": str(e)
        }
