#!/usr/bin/env python3
"""
Standalone audio generation test.
Generates audio from a text note without database.
"""

import asyncio
import os
import wave


async def test_audio_generation():
    """Generate audio from sample text."""
    
    # Sample text note (you can replace this with your own)
    text_note = """
    Neural networks are computational models inspired by biological neural networks in the brain.
    They consist of layers of interconnected nodes, called neurons, that process information.
    
    The basic structure includes an input layer, one or more hidden layers, and an output layer.
    Each connection between neurons has a weight that determines the strength of the signal.
    
    Training a neural network involves adjusting these weights through a process called backpropagation.
    This allows the network to learn patterns from data and make predictions on new inputs.
    
    Common applications include image recognition, natural language processing, and recommendation systems.
    """
    
    print("="*80)
    print("🎧 AUDIO GENERATION TEST")
    print("="*80)
    
    print(f"\n📝 Text to convert:")
    print(f"   Length: {len(text_note)} characters")
    print(f"   Words: {len(text_note.split())} words")
    print(f"   Preview: {text_note[:100]}...")
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: GEMINI_API_KEY environment variable not set")
        print("\nTo set it:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        return False
    
    print(f"\n✅ API key found: {api_key[:20]}...")
    
    # Import Gemini client
    try:
        from google import genai
        from google.genai import types
        print("✅ Gemini SDK imported")
    except ImportError as e:
        print(f"\n❌ ERROR: Failed to import Gemini SDK: {e}")
        print("\nTo install:")
        print("  pip install google-genai")
        return False
    
    # Initialize client
    client = genai.Client(api_key=api_key)
    print("✅ Gemini client initialized")
    
    # Voice selection
    voice_name = "Kore"  # Warm, coaching voice
    style_prompt = "Read this in an encouraging, motivational tone. Use a warm, supportive voice that guides the listener through the material with enthusiasm."
    
    print(f"\n🎤 Voice: {voice_name}")
    print(f"   Style: {style_prompt[:60]}...")
    
    # Generate audio
    print("\n🔄 Generating audio...")
    
    try:
        prompt = f"{style_prompt}\n\n{text_note}"
        
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
        
        print(f"✅ Audio generated!")
        print(f"   Size: {len(audio_data):,} bytes")
        
        # Save to file
        output_dir = "storage/audio"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/test_audio_{voice_name}.wav"
        
        with wave.open(output_file, "wb") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(24000)  # 24kHz
            wf.writeframes(audio_data)
        
        # Calculate duration
        duration_seconds = len(audio_data) / (24000 * 2 * 1)
        duration_minutes = duration_seconds / 60
        
        print(f"\n✅ Audio saved to: {output_file}")
        print(f"   Duration: {duration_seconds:.1f} seconds ({duration_minutes:.1f} minutes)")
        print(f"   File size: {os.path.getsize(output_file):,} bytes")
        
        print("\n🎵 To play the audio:")
        print(f"   open {output_file}")
        print(f"   # or")
        print(f"   afplay {output_file}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Audio generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_custom_text():
    """Generate audio from custom text provided by user."""
    
    print("\n" + "="*80)
    print("📝 CUSTOM TEXT INPUT")
    print("="*80)
    print("\nEnter your text (press Ctrl+D when done):")
    print("-" * 80)
    
    try:
        import sys
        lines = []
        for line in sys.stdin:
            lines.append(line)
        custom_text = ''.join(lines)
        
        if not custom_text.strip():
            print("No text provided, using sample text instead.")
            return await test_audio_generation()
        
        print(f"\n✅ Received {len(custom_text)} characters")
        # Generate audio with custom text...
        
    except KeyboardInterrupt:
        print("\n\nUsing sample text instead.")
        return await test_audio_generation()


if __name__ == "__main__":
    print("\n🎧 Audio Generation - Standalone Test")
    print("="*80)
    print("This script generates audio from text without needing the database.")
    print("="*80)
    
    success = asyncio.run(test_audio_generation())
    
    if success:
        print("\n" + "="*80)
        print("✅ TEST SUCCESSFUL!")
        print("="*80)
        print("\n📊 What was tested:")
        print("  ✅ Gemini TTS API connection")
        print("  ✅ Audio generation from text")
        print("  ✅ WAV file creation")
        print("  ✅ Duration calculation")
        
        print("\n🎯 Next steps:")
        print("  1. Play the audio file to verify quality")
        print("  2. Try different voices (Puck, Charon, Fenrir)")
        print("  3. Test with longer text")
        print("  4. Test chunking with >95k character text")
    else:
        print("\n" + "="*80)
        print("❌ TEST FAILED")
        print("="*80)
        print("\nCheck the error messages above for details.")
