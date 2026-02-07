#!/usr/bin/env python3
"""
Test audio generation with longer text and different voice.
"""

import asyncio
import os
import wave


async def test_long_audio_puck():
    """Generate audio from longer text with Puck voice (textbook tone)."""
    
    # Longer text about machine learning (approximately 500 words)
    long_text = """
    Machine learning is a subset of artificial intelligence that focuses on developing algorithms 
    and statistical models that enable computers to improve their performance on tasks through experience.
    Unlike traditional programming where explicit instructions are provided, machine learning systems 
    learn patterns from data and make predictions or decisions based on those patterns.
    
    There are three main categories of machine learning: supervised learning, unsupervised learning, 
    and reinforcement learning. Supervised learning involves training models on labeled data, where 
    the correct output is known for each input. Common applications include image classification, 
    spam detection, and price prediction. The model learns to map inputs to outputs by minimizing 
    the difference between its predictions and the actual labels.
    
    Unsupervised learning, in contrast, works with unlabeled data. The algorithm must discover 
    patterns and structures in the data without explicit guidance. Clustering algorithms group 
    similar data points together, while dimensionality reduction techniques compress high-dimensional 
    data into lower dimensions while preserving important information. These methods are valuable 
    for exploratory data analysis and feature extraction.
    
    Reinforcement learning takes a different approach, where an agent learns to make decisions by 
    interacting with an environment. The agent receives rewards or penalties based on its actions 
    and learns to maximize cumulative rewards over time. This paradigm has achieved remarkable 
    success in game playing, robotics, and autonomous systems.
    
    Neural networks represent a powerful class of machine learning models inspired by biological 
    neural networks in the brain. They consist of interconnected layers of artificial neurons that 
    process information through weighted connections. Deep learning, which uses neural networks 
    with many layers, has revolutionized fields like computer vision, natural language processing, 
    and speech recognition.
    
    The training process for machine learning models typically involves several key steps. First, 
    data must be collected and preprocessed to ensure quality and consistency. Features are then 
    extracted or engineered to represent the data in a format suitable for the algorithm. The model 
    is trained using an optimization algorithm that adjusts its parameters to minimize a loss function. 
    Finally, the model is evaluated on separate test data to assess its generalization performance.
    
    Overfitting is a common challenge in machine learning, occurring when a model learns the training 
    data too well, including its noise and peculiarities, resulting in poor performance on new data. 
    Regularization techniques, cross-validation, and proper train-test splits help mitigate this issue.
    
    The field continues to evolve rapidly, with recent advances in transfer learning, few-shot learning, 
    and self-supervised learning pushing the boundaries of what's possible with limited labeled data.
    """
    
    print("="*80)
    print("🎧 LONG AUDIO TEST - PUCK VOICE (Textbook Tone)")
    print("="*80)
    
    print(f"\n📝 Text to convert:")
    print(f"   Length: {len(long_text):,} characters")
    print(f"   Words: {len(long_text.split())} words")
    print(f"   Estimated reading time: ~{len(long_text.split()) // 200} minutes")
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: GEMINI_API_KEY not set")
        return False
    
    print(f"\n✅ API key found")
    
    # Import Gemini
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=api_key)
    print("✅ Gemini client initialized")
    
    # Use Puck voice (textbook tone)
    voice_name = "Puck"
    style_prompt = "Read this in a clear, authoritative academic tone. Speak with precision and formality, as if lecturing in a university."
    
    print(f"\n🎤 Voice: {voice_name} (Textbook - authoritative)")
    print(f"   Style: {style_prompt[:60]}...")
    
    # Generate audio
    print("\n🔄 Generating audio (this may take 10-20 seconds)...")
    
    try:
        prompt = f"{style_prompt}\n\n{long_text}"
        
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
        
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        
        print(f"✅ Audio generated!")
        print(f"   Size: {len(audio_data):,} bytes")
        
        # Save to file
        output_dir = "storage/audio"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/test_long_{voice_name}.wav"
        
        with wave.open(output_file, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_data)
        
        duration_seconds = len(audio_data) / (24000 * 2 * 1)
        duration_minutes = duration_seconds / 60
        
        print(f"\n✅ Audio saved to: {output_file}")
        print(f"   Duration: {duration_seconds:.1f} seconds ({duration_minutes:.1f} minutes)")
        print(f"   File size: {os.path.getsize(output_file):,} bytes")
        
        print("\n🎵 To play:")
        print(f"   afplay {output_file}")
        
        print("\n📊 Comparison:")
        print(f"   Reading time: ~{len(long_text.split()) // 200} minutes")
        print(f"   Audio time: {duration_minutes:.1f} minutes")
        print(f"   Ratio: Audio is {duration_minutes / (len(long_text.split()) // 200):.1f}x reading time")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🎧 Long Audio Test - Puck Voice")
    print("="*80)
    print("Testing with ~500 words of machine learning content")
    print("Voice: Puck (authoritative, textbook tone)")
    print("="*80)
    
    success = asyncio.run(test_long_audio_puck())
    
    if success:
        print("\n" + "="*80)
        print("✅ LONG AUDIO TEST SUCCESSFUL!")
        print("="*80)
        print("\n📊 What was tested:")
        print("  ✅ Longer content (~500 words)")
        print("  ✅ Different voice (Puck vs Kore)")
        print("  ✅ Textbook tone (authoritative)")
        print("  ✅ Duration calculation for longer audio")
        
        print("\n🎯 Compare the voices:")
        print("  1. Play storage/audio/test_audio_Kore.wav (warm, coaching)")
        print("  2. Play storage/audio/test_long_Puck.wav (authoritative, textbook)")
        print("  3. Notice the difference in tone and style!")
    else:
        print("\n❌ Test failed")
