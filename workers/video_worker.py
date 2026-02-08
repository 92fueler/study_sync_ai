"""
Video Worker - Processes video generation jobs using Veo 3 API

This worker polls for pending video segments and generates them using Veo 3.
"""

import os
import time
import asyncio
import logging
import asyncpg
from google import genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Veo client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


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
                WHERE vs.status = 'pending'
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
            
            # Call Veo 3 API
            # NOTE: This is pseudocode - actual Veo API syntax may differ
            try:
                operation = client.models.generate_video(
                    model="veo-3.1",
                    prompt=segment['prompt'],
                    config={
                        "duration_seconds": 8,
                        "resolution": "720p",
                        "aspect_ratio": "16:9"
                    }
                )
                
                # Store operation ID
                await conn.execute(
                    "UPDATE video_segments SET operation_id = $1 WHERE id = $2",
                    operation.name,
                    segment['id']
                )
                
                # Poll for completion (in separate task)
                asyncio.create_task(poll_operation(conn, segment['id'], operation.name, segment['segment_path']))
                
            except Exception as e:
                logger.error(f"Failed to start video generation: {e}")
                await conn.execute(
                    "UPDATE video_segments SET status = 'failed', error_message = $1 WHERE id = $2",
                    str(e),
                    segment['id']
                )
            
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)


async def poll_operation(conn, segment_id, operation_id, segment_path):
    """Poll Veo operation until complete"""
    max_attempts = 60  # 10 minutes max
    
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
            f.write(f"file '{seg['segment_path']}'\n")
    
    # Get output path
    output_path = await conn.fetchval(
        "SELECT video_path FROM video_artifacts WHERE id = $1",
        video_id
    )
    
    # Stitch with ffmpeg
    try:
        subprocess.run([
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
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
            "UPDATE video_artifacts SET status = 'failed' WHERE id = $1",
            video_id
        )


if __name__ == "__main__":
    asyncio.run(process_video_segments())
