#!/usr/bin/env python3
"""
E2E Test: Ingestion → Synthesis with Audio Generation

Tests the complete flow:
1. Ingest content
2. Create user profile with audio format preference
3. Generate artifact with synthesis agent
4. Verify audio is generated with correct cognitive tone
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
import hashlib
from agents.ingestion.tools import ingest_content
from agents.synthesis.tools import generate_artifact
from agents.profile.tools import create_profile


async def cleanup_test_data(user_id: str):
    """Clean up test data from previous runs."""
    dsn = os.getenv("SUPABASE_URL")
    conn = await asyncpg.connect(dsn)
    try:
        # Delete in reverse dependency order
        await conn.execute("DELETE FROM audio_artifacts WHERE artifact_id IN (SELECT id FROM artifacts WHERE user_id = $1)", user_id)
        await conn.execute("DELETE FROM artifacts WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM user_materials WHERE user_id = $1", user_id)
        await conn.execute("DELETE FROM user_profiles WHERE user_id = $1", user_id)
        print(f"✓ Cleaned up test data for user {user_id}")
    finally:
        await conn.close()


async def verify_audio_generated(artifact_id: str, expected_tone: str):
    """Verify that audio was generated with the correct voice."""
    dsn = os.getenv("SUPABASE_URL")
    conn = await asyncpg.connect(dsn)
    try:
        # Wait for async audio generation to complete
        await asyncio.sleep(10)
        
        row = await conn.fetchrow(
            "SELECT audio_path, voice_name FROM audio_artifacts WHERE artifact_id = $1",
            artifact_id
        )
        
        if not row:
            print(f"✗ No audio found for artifact {artifact_id}")
            return False
        
        # Check if voice matches expected tone
        from agents.synthesis.audio import _get_voice_for_tone
        expected_voice = _get_voice_for_tone(expected_tone)
        
        if row['voice_name'] == expected_voice:
            print(f"✓ Audio generated with correct voice: {row['voice_name']} (tone: {expected_tone})")
            print(f"  Path: {row['audio_path']}")
            return True
        else:
            print(f"✗ Audio voice mismatch: expected {expected_voice}, got {row['voice_name']}")
            return False
    finally:
        await conn.close()


async def main():
    print("=" * 60)
    print("E2E Test: Ingestion → Synthesis → Audio Generation")
    print("=" * 60)
    
    test_user_id = "test-e2e-tts-user"
    
    # Step 0: Cleanup
    print("\n[Step 0] Cleaning up previous test data...")
    await cleanup_test_data(test_user_id)
    
    # Step 1: Create user profile with audio format preference
    print("\n[Step 1] Creating user profile with audio format and coaching tone...")
    profile_result = create_profile(
        user_id=test_user_id,
        display_name="E2E Test User",
        style_dna={
            "tone": "coaching",  # Should map to "Kore" voice
            "format_pref": "outline",
            "uses_emoji": True,
            "prefers_diagrams": True,
            "formats": ["audio", "notes"],  # Audio format enabled
            "learning_preferences": ["analogies", "real_world"]
        },
        goals=["Test audio generation"]
    )
    
    if profile_result["status"] != "success":
        print(f"✗ Profile creation failed: {profile_result.get('error')}")
        return 1
    
    print(f"✓ Profile created: {profile_result['profile_id']}")
    
    # Step 2: Ingest test content
    print("\n[Step 2] Ingesting test content...")
    test_content = """
    Neural Networks: A Beginner's Guide
    
    Neural networks are computational models inspired by the human brain. They consist of layers of interconnected nodes (neurons) that process information.
    
    Key Concepts:
    1. Layers: Input layer, hidden layers, and output layer
    2. Weights: Connection strengths between neurons
    3. Activation Functions: Determine neuron output (e.g., ReLU, sigmoid)
    4. Backpropagation: Algorithm for training the network
    
    Applications:
    - Image recognition
    - Natural language processing
    - Recommendation systems
    - Autonomous vehicles
    """
    
    content_hash = hashlib.sha256(test_content.encode()).hexdigest()
    
    ingest_result = await ingest_content(
        user_id=test_user_id,
        content_hash=content_hash,
        filename="Neural Networks Guide",
        media_type="TXT",
        content_text=test_content
    )
    
    if ingest_result["status"] != "success":
        print(f"✗ Ingestion failed: {ingest_result.get('error')}")
        return 1
    
    content_id = ingest_result["content_id"]
    print(f"✓ Content ingested: {content_id}")
    
    # Step 3: Generate artifact with synthesis agent
    print("\n[Step 3] Generating personalized study artifact...")
    print("  (This should automatically trigger audio generation)")
    
    synthesis_result = generate_artifact(
        user_id=test_user_id,
        content_ids=[content_id],
        profile_version=1,
        style_dna={
            "tone": "coaching",
            "format_pref": "outline",
            "uses_emoji": True,
            "prefers_diagrams": True,
            "formats": ["audio", "notes"],
            "learning_preferences": ["analogies", "real_world"]
        },
        time_available_minutes=10
    )
    
    if synthesis_result["status"] != "success":
        print(f"✗ Synthesis failed: {synthesis_result.get('error')}")
        return 1
    
    artifact_id = synthesis_result["artifact_id"]
    print(f"✓ Artifact generated: {artifact_id}")
    print(f"  Estimated reading time: {synthesis_result.get('estimated_minutes')} minutes")
    print(f"  Content preview: {synthesis_result['content'][:200]}...")
    
    # Step 4: Verify audio was generated
    print("\n[Step 4] Verifying audio generation...")
    audio_ok = await verify_audio_generated(artifact_id, "coaching")
    
    if not audio_ok:
        print("\n✗ E2E TEST FAILED: Audio not generated correctly")
        return 1
    
    # Success!
    print("\n" + "=" * 60)
    print("✓ E2E TEST PASSED")
    print("=" * 60)
    print("\nSummary:")
    print(f"  User: {test_user_id}")
    print(f"  Content: {content_id}")
    print(f"  Artifact: {artifact_id}")
    print(f"  Cognitive Tone: coaching → Voice: Kore")
    print(f"  Formats: audio, notes")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
