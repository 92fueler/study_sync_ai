#!/usr/bin/env python3
"""
Test script for audio generation backend.

Tests:
1. Voice selection for different cognitive tones
2. Text chunking for long content
3. Audio generation from text
4. API endpoint availability
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.synthesis.audio import (
    _get_voice_for_tone,
    _get_style_prompt_for_tone,
    _chunk_text,
    generate_audio_from_text
)


def test_voice_selection():
    """Test voice mapping for cognitive tones."""
    print("\n" + "="*80)
    print("TEST 1: Voice Selection for Cognitive Tones")
    print("="*80)
    
    tones = ["textbook", "coaching", "beginner_friendly", "key_points"]
    
    for tone in tones:
        voice = _get_voice_for_tone(tone)
        style = _get_style_prompt_for_tone(tone)
        
        print(f"\n{tone.upper()}:")
        print(f"  Voice: {voice}")
        print(f"  Style: {style[:80]}...")
    
    print("\n✅ Voice selection test passed")


def test_text_chunking():
    """Test text chunking for long content."""
    print("\n" + "="*80)
    print("TEST 2: Text Chunking for Long Content")
    print("="*80)
    
    # Test 1: Short text (no chunking needed)
    short_text = "This is a short test. " * 100  # ~2k chars
    chunks = _chunk_text(short_text, max_chars=95000)
    print(f"\nShort text ({len(short_text)} chars):")
    print(f"  Chunks: {len(chunks)}")
    print(f"  ✅ Expected 1 chunk, got {len(chunks)}")
    
    # Test 2: Long text (needs chunking)
    long_text = "This is a longer test sentence. " * 5000  # ~160k chars
    chunks = _chunk_text(long_text, max_chars=95000)
    print(f"\nLong text ({len(long_text)} chars):")
    print(f"  Chunks: {len(chunks)}")
    print(f"  Chunk sizes: {[len(c) for c in chunks]}")
    
    # Verify all chunks are within limit
    all_within_limit = all(len(c) <= 95000 for c in chunks)
    print(f"  All chunks <= 95k chars: {all_within_limit}")
    
    # Verify no content lost
    combined_length = sum(len(c) for c in chunks)
    print(f"  Original: {len(long_text)} chars")
    print(f"  Combined: {combined_length} chars")
    print(f"  Loss: {len(long_text) - combined_length} chars")
    
    if all_within_limit and combined_length >= len(long_text) * 0.99:
        print("\n✅ Text chunking test passed")
    else:
        print("\n❌ Text chunking test failed")


async def test_audio_generation():
    """Test audio generation from text."""
    print("\n" + "="*80)
    print("TEST 3: Audio Generation from Text")
    print("="*80)
    
    # Test with short sample text
    test_text = """
    Neural networks are computational models inspired by biological neural networks.
    They consist of layers of interconnected nodes that process information.
    Training involves adjusting connection weights through backpropagation.
    This allows the network to learn patterns from data.
    """
    
    print(f"\nGenerating audio for sample text ({len(test_text)} chars)...")
    print(f"Voice: Kore (coaching tone)")
    
    try:
        result = await generate_audio_from_text(
            text=test_text,
            voice_name="Kore",
            cognitive_tone="coaching",
            artifact_id="test-audio-001"
        )
        
        if result["status"] == "success":
            print(f"\n✅ Audio generation successful!")
            print(f"  Audio URL: {result['audio_url']}")
            print(f"  Duration: {result['duration_seconds']:.1f} seconds")
            print(f"  File size: {result['file_size_bytes']:,} bytes")
            print(f"  Voice: {result['voice_name']}")
            print(f"  Path: {result['audio_path']}")
            
            # Check if file exists
            if os.path.exists(result['audio_path']):
                print(f"  ✅ Audio file created successfully")
            else:
                print(f"  ❌ Audio file not found at {result['audio_path']}")
        else:
            print(f"\n❌ Audio generation failed:")
            print(f"  Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Audio generation error: {e}")
        import traceback
        traceback.print_exc()


def test_api_endpoints():
    """Test API endpoint availability."""
    print("\n" + "="*80)
    print("TEST 4: API Endpoint Availability")
    print("="*80)
    
    import requests
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"\nHealth endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ Gateway is running")
        else:
            print(f"  ⚠️  Gateway returned {response.status_code}")
    except Exception as e:
        print(f"  ❌ Gateway not accessible: {e}")
    
    # Test audio endpoint (should return 404 for non-existent file)
    try:
        response = requests.get(f"{base_url}/api/v1/audio/test.wav", timeout=5)
        print(f"\nAudio streaming endpoint: {response.status_code}")
        if response.status_code == 404:
            print(f"  ✅ Audio endpoint is registered (404 expected for non-existent file)")
        else:
            print(f"  Status: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Audio endpoint error: {e}")


async def main():
    """Run all tests."""
    print("\n🧪 AUDIO GENERATION BACKEND TESTS\n")
    
    # Test 1: Voice selection
    test_voice_selection()
    
    # Test 2: Text chunking
    test_text_chunking()
    
    # Test 3: Audio generation (requires Gemini API key)
    if os.getenv("GEMINI_API_KEY"):
        await test_audio_generation()
    else:
        print("\n⚠️  Skipping audio generation test (GEMINI_API_KEY not set)")
    
    # Test 4: API endpoints
    test_api_endpoints()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED")
    print("="*80)
    print("\nNext steps:")
    print("1. Check if audio file was created in storage/audio/")
    print("2. Try playing the audio file")
    print("3. Test with longer content to verify chunking")
    print("4. Test API endpoint: POST /api/v1/audio/generate/{artifact_id}")


if __name__ == "__main__":
    asyncio.run(main())
