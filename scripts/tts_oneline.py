#!/usr/bin/env python3
"""
One-line TTS test - just provide text as argument.
Usage: python scripts/tts_oneline.py "Your text here" [voice]
"""

import asyncio
import os
import sys
import wave
from google import genai
from google.genai import types


async def tts(text, voice="Kore"):
    """Generate audio from text."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            )
        )
    )
    
    audio_data = response.candidates[0].content.parts[0].inline_data.data
    
    # Save
    os.makedirs("storage/audio", exist_ok=True)
    output = f"storage/audio/quick_{voice}.wav"
    
    with wave.open(output, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(audio_data)
    
    duration = len(audio_data) / (24000 * 2)
    print(f"✅ {output} ({duration:.1f}s)")
    return output


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/tts_oneline.py 'Your text here' [voice]")
        print("Voices: Kore (default), Puck, Charon, Fenrir")
        sys.exit(1)
    
    text = sys.argv[1]
    voice = sys.argv[2] if len(sys.argv) > 2 else "Kore"
    
    asyncio.run(tts(text, voice))
