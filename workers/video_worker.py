"""
Video Worker - Processes video generation jobs using Veo 3 API

This worker polls for pending video segments and generates them using Veo 3.
"""

import os
import time
import asyncio
import logging
import subprocess
import asyncpg
from google import genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Veo client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
VIDEO_PROVIDER = os.getenv("VIDEO_PROVIDER", "placeholder").strip().lower()
USE_PLACEHOLDER_ON_FAILURE = os.getenv("VIDEO_PLACEHOLDER_ON_FAILURE", "1").strip() in {"1", "true", "yes"}
VEO_MODEL = os.getenv("VEO_MODEL", "veo-3.1-generate-preview").strip()
THEMES = [
    {"name": "RAINBOW", "bg": "0x2d1b69", "a1": "0xff006e", "a2": "0x8338ec", "a3": "0x3a86ff"},
    {"name": "ICE CREAM", "bg": "0x542344", "a1": "0xffafcc", "a2": "0xffcad4", "a3": "0xbde0fe"},
    {"name": "CANDY LAND", "bg": "0x3d2c8d", "a1": "0xff7b00", "a2": "0xffe100", "a3": "0x70e000"},
    {"name": "AURORA", "bg": "0x0b132b", "a1": "0x5bc0be", "a2": "0x6fffe9", "a3": "0x9b5de5"},
    {"name": "SUNSET POP", "bg": "0x370617", "a1": "0xf48c06", "a2": "0xffba08", "a3": "0xe85d04"},
]


def _format_generation_error(error: Exception) -> str:
    """Normalize provider errors into user-readable messages."""
    message = str(error)
    lower = message.lower()
    if "429" in lower or "resource_exhausted" in lower or "quota" in lower:
        return (
            "429 RESOURCE_EXHAUSTED: Video generation quota exceeded for Veo. "
            "Please retry later or upgrade quota."
        )
    return message


async def _mark_video_failed(conn: asyncpg.Connection, segment_id: str, error_message: str) -> None:
    """Propagate a segment failure to the parent video and remaining segments."""
    video_id = await conn.fetchval(
        "SELECT video_artifact_id FROM video_segments WHERE id = $1",
        segment_id,
    )
    if not video_id:
        return

    await conn.execute(
        "UPDATE video_segments SET status = 'failed', error_message = $1 WHERE id = $2",
        error_message,
        segment_id,
    )

    await conn.execute(
        """
        UPDATE video_segments
        SET status = 'failed',
            error_message = COALESCE(error_message, 'Aborted after video-level failure')
        WHERE video_artifact_id = $1
          AND status IN ('pending', 'generating')
        """,
        video_id,
    )

    await conn.execute(
        "UPDATE video_artifacts SET status = 'failed', error_message = $1 WHERE id = $2",
        error_message,
        video_id,
    )


def _pick_fontfile() -> str:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return ""


async def process_video_segments():
    """
    Main worker loop - polls for pending segments and generates them
    """
    dsn = os.getenv("SUPABASE_URL")
    conn = await asyncpg.connect(dsn)
    
    logger.info("Video worker started, polling for segments...")
    
    while True:
        try:
            # Get next pending segment
            segment = await conn.fetchrow(
                """
                SELECT vs.id, vs.video_artifact_id, vs.segment_index,
                       vs.prompt, vs.segment_path
                FROM video_segments vs
                JOIN video_artifacts va ON va.id = vs.video_artifact_id
                WHERE vs.status = 'pending'
                  AND va.status = 'generating'
                ORDER BY vs.segment_index
                LIMIT 1
                """
            )
            
            if not segment:
                await asyncio.sleep(10)  # No work, wait
                continue
            
            # Mark as generating
            await conn.execute(
                "UPDATE video_segments SET status = 'generating' WHERE id = $1",
                segment['id']
            )
            
            logger.info(f"Generating segment {segment['segment_index']}...")
            
            # Call Veo 3 API or deterministic placeholder generation
            try:
                if VIDEO_PROVIDER == "placeholder":
                    file_size = await _generate_placeholder_segment(
                        segment["segment_path"],
                        segment_index=int(segment["segment_index"]),
                        prompt=str(segment["prompt"] or ""),
                        duration_seconds=8,
                    )
                    await conn.execute(
                        "UPDATE video_segments SET status = 'ready', file_size_bytes = $1 WHERE id = $2",
                        file_size,
                        segment["id"],
                    )
                    logger.info(
                        f"Segment {segment['segment_index']} complete (placeholder)! ({file_size} bytes)"
                    )
                    await check_video_complete(conn, segment["id"])
                else:
                    operation = client.models.generate_videos(
                        model=VEO_MODEL,
                        prompt=segment["prompt"],
                        config={
                            "duration_seconds": 8,
                            "resolution": "720p",
                            "aspect_ratio": "16:9",
                        },
                    )

                    operation_name = getattr(operation, "name", None)
                    if operation_name:
                        await conn.execute(
                            "UPDATE video_segments SET operation_id = $1 WHERE id = $2",
                            operation_name,
                            segment["id"],
                        )

                    max_attempts = 60  # 10 minutes max
                    for _ in range(max_attempts):
                        if operation.done:
                            break
                        await asyncio.sleep(10)
                        operation = client.operations.get(operation)

                    if not operation.done:
                        raise TimeoutError("Timed out waiting for Veo generation to complete")

                    if operation.error:
                        raise RuntimeError(str(operation.error))

                    generated_videos = getattr(operation.result, "generated_videos", None) or []
                    if not generated_videos:
                        raise RuntimeError("Veo returned no generated videos")

                    video_obj = generated_videos[0].video
                    video_data = client.files.download(file=video_obj)

                    os.makedirs(os.path.dirname(segment["segment_path"]), exist_ok=True)
                    with open(segment["segment_path"], "wb") as f:
                        f.write(video_data)

                    file_size = len(video_data)
                    await conn.execute(
                        "UPDATE video_segments SET status = 'ready', file_size_bytes = $1 WHERE id = $2",
                        file_size,
                        segment["id"],
                    )

                    logger.info(
                        f"Segment {segment['segment_index']} complete! ({file_size} bytes)"
                    )
                    await check_video_complete(conn, segment["id"])
                
            except Exception as e:
                logger.error(f"Failed to start video generation: {e}")
                if USE_PLACEHOLDER_ON_FAILURE:
                    try:
                        file_size = await _generate_placeholder_segment(
                            segment["segment_path"],
                            segment_index=int(segment["segment_index"]),
                            prompt=str(segment["prompt"] or ""),
                            duration_seconds=8,
                        )
                        await conn.execute(
                            """
                            UPDATE video_segments
                            SET status = 'ready', file_size_bytes = $1, error_message = $2
                            WHERE id = $3
                            """,
                            file_size,
                            f"Veo failed, used placeholder: {e}",
                            segment["id"],
                        )
                        logger.info(
                            f"Segment {segment['segment_index']} completed via fallback placeholder ({file_size} bytes)"
                        )
                        await check_video_complete(conn, segment["id"])
                    except Exception as fallback_error:
                        await _mark_video_failed(
                            conn,
                            segment["id"],
                            _format_generation_error(
                                RuntimeError(f"{e}; fallback failed: {fallback_error}")
                            ),
                        )
                else:
                    await _mark_video_failed(conn, segment["id"], _format_generation_error(e))
            
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)


async def poll_operation(segment_id, operation_id, segment_path):
    """Poll Veo operation until complete"""
    dsn = os.getenv("SUPABASE_URL")
    conn = await asyncpg.connect(dsn)
    max_attempts = 60  # 10 minutes max
    
    try:
        for attempt in range(max_attempts):
            try:
                # Check operation status
                operation = client.operations.get(name=operation_id)
                
                if operation.done:
                    if operation.error:
                        logger.error(f"Segment {segment_id} failed: {operation.error}")
                        await conn.execute(
                            "UPDATE video_segments SET status = 'failed', error_message = $1 WHERE id = $2",
                            str(operation.error),
                            segment_id
                        )
                    else:
                        # Download video
                        video_data = operation.result.video
                        
                        # Save to disk
                        os.makedirs(os.path.dirname(segment_path), exist_ok=True)
                        with open(segment_path, 'wb') as f:
                            f.write(video_data)
                        
                        file_size = len(video_data)
                        
                        await conn.execute(
                            "UPDATE video_segments SET status = 'ready', file_size_bytes = $1 WHERE id = $2",
                            file_size,
                            segment_id
                        )
                        
                        logger.info(f"Segment {segment_id} complete! ({file_size} bytes)")
                        
                        # Check if all segments done
                        await check_video_complete(conn, segment_id)
                    
                    break
                
                await asyncio.sleep(10)  # Poll every 10 seconds
                
            except Exception as e:
                logger.error(f"Poll error for segment {segment_id}: {e}")
                await asyncio.sleep(10)
    finally:
        await conn.close()


async def check_video_complete(conn, segment_id):
    """Check if all segments for a video are complete, then stitch"""
    video_id = await conn.fetchval(
        "SELECT video_artifact_id FROM video_segments WHERE id = $1",
        segment_id
    )
    
    pending = await conn.fetchval(
        "SELECT COUNT(*) FROM video_segments WHERE video_artifact_id = $1 AND status != 'ready'",
        video_id
    )
    
    if pending == 0:
        logger.info(f"All segments complete for video {video_id}, stitching...")
        await stitch_video(conn, video_id)


async def stitch_video(conn, video_id):
    """Stitch all segments into final video using ffmpeg"""
    import subprocess
    
    # Get all segments in order
    segments = await conn.fetch(
        "SELECT segment_path FROM video_segments WHERE video_artifact_id = $1 ORDER BY segment_index",
        video_id
    )
    
    # Create concat file for ffmpeg
    concat_file = f"/tmp/concat_{video_id}.txt"
    with open(concat_file, 'w') as f:
        for seg in segments:
            # Concat paths are resolved relative to concat file location (/tmp), so use absolute paths.
            abs_seg_path = os.path.abspath(seg["segment_path"])
            f.write(f"file '{abs_seg_path}'\n")
    
    # Get output path
    output_path = await conn.fetchval(
        "SELECT video_path FROM video_artifacts WHERE id = $1",
        video_id
    )
    output_path = os.path.abspath(output_path)
    
    # Stitch with ffmpeg
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        subprocess.run([
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            '-y',
            output_path
        ], check=True)
        
        # Update video artifact
        file_size = os.path.getsize(output_path)
        await conn.execute(
            "UPDATE video_artifacts SET status = 'ready', file_size_bytes = $1 WHERE id = $2",
            file_size,
            video_id
        )
        
        logger.info(f"Video {video_id} complete! ({file_size} bytes)")
        
    except Exception as e:
        logger.error(f"Failed to stitch video {video_id}: {e}")
        await conn.execute(
            "UPDATE video_artifacts SET status = 'failed', error_message = $1 WHERE id = $2",
            str(e),
            video_id,
        )


async def _generate_placeholder_segment(
    segment_path: str,
    segment_index: int,
    prompt: str,
    duration_seconds: int = 8,
) -> int:
    """
    Create a deterministic placeholder MP4 segment so the pipeline can complete in smoke/dev runs.
    """
    os.makedirs(os.path.dirname(segment_path), exist_ok=True)
    theme = THEMES[segment_index % len(THEMES)]
    prompt_lower = prompt.lower()
    if "rainbow" in prompt_lower:
        theme = THEMES[0]
    elif "ice cream" in prompt_lower or "icecream" in prompt_lower:
        theme = THEMES[1]

    font = _pick_fontfile()
    drawtext_font = f"fontfile={font}:" if font else ""

    # Moving color blocks + labeled cards so smoke videos are visibly non-black.
    vf = (
        f"drawbox=x=0:y=0:w=iw:h=ih:color={theme['bg']}:t=fill,"
        "drawbox=x='mod(t*220,iw)-240':y=80:w=240:h=220:color="
        f"{theme['a1']}@0.9:t=fill,"
        "drawbox=x='iw-mod(t*180,iw)':y=360:w=220:h=220:color="
        f"{theme['a2']}@0.9:t=fill,"
        "drawbox=x='(iw-320)/2':y='(ih-200)/2':w=320:h=200:color="
        f"{theme['a3']}@0.75:t=fill,"
        f"drawtext={drawtext_font}text='{theme['name']}':fontsize=68:fontcolor=white:"
        "x=(w-text_w)/2:y=70:box=1:boxcolor=black@0.4:boxborderw=14,"
        f"drawtext={drawtext_font}text='SEGMENT {segment_index:02d}':fontsize=32:fontcolor=white:"
        "x=(w-text_w)/2:y=h-90:box=1:boxcolor=black@0.35:boxborderw=10"
    )

    cmd = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s=1280x720:r=25:d={duration_seconds}",
        "-vf",
        vf,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-y",
        segment_path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return os.path.getsize(segment_path)


if __name__ == "__main__":
    asyncio.run(process_video_segments())
