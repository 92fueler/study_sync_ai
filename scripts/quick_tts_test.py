#!/usr/bin/env python3
"""
Quick TTS test - paste your text and generate audio.
"""

import asyncio
import os
import wave
from google import genai
from google.genai import types


async def generate_audio_from_text(text, voice="Kore", output_name="my_audio"):
    """Generate audio from text."""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return False
    
    client = genai.Client(api_key=api_key)
    
    # Voice descriptions
    voices = {
        "Kore": "warm, encouraging, coaching",
        "Puck": "authoritative, academic, textbook",
        "Charon": "friendly, patient, beginner-friendly",
        "Fenrir": "direct, efficient, concise"
    }
    
    print(f"\n🎤 Voice: {voice} ({voices.get(voice, 'unknown')})")
    print(f"📝 Text length: {len(text)} chars, {len(text.split())} words")
    print(f"⏱️  Estimated audio: ~{len(text.split()) / 150:.1f} minutes")
    print("\n🔄 Generating audio...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    )
                )
            )
        )
        
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        
        # Save audio
        output_dir = "storage/audio"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/{output_name}_{voice}.wav"
        
        with wave.open(output_file, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_data)
        
        duration = len(audio_data) / (24000 * 2)
        
        print(f"\n✅ Audio generated!")
        print(f"📁 File: {output_file}")
        print(f"⏱️  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"💾 Size: {os.path.getsize(output_file):,} bytes")
        print(f"\n🎵 Play with: afplay {output_file}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    print("="*80)
    print("🎧 Quick TTS Test")
    print("="*80)
    
    # Get text from user
    print("\n📝 Enter your text (or paste from clipboard):")
    print("   (Press Ctrl+D or Ctrl+Z when done)")
    print("-"*80)
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    text = '\n'.join(lines).strip()
    
    if not text:
        print("\n❌ No text provided!")
        return
    
    # Choose voice
    print("\n🎤 Choose voice:")
    print("  1. Kore (warm, coaching)")
    print("  2. Puck (authoritative, textbook)")
    print("  3. Charon (friendly, beginner)")
    print("  4. Fenrir (direct, concise)")
    
    choice = input("\nEnter number (default: 1): ").strip() or "1"
    
    voices = {"1": "Kore", "2": "Puck", "3": "Charon", "4": "Fenrir"}
    voice = voices.get(choice, "Kore")
    
    # Generate
    asyncio.run(generate_audio_from_text(text, voice))


if __name__ == "__main__":
    main()
