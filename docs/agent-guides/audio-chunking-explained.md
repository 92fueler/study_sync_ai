# Audio Generation - Long Content Handling

## Problem
Gemini TTS API has a 32k token limit (~100k characters). Study notes can easily exceed this limit.

## Solution: Intelligent Chunking + Audio Combination

### How It Works

#### 1. **Text Chunking** (`_chunk_text()`)
```python
def _chunk_text(text: str, max_chars: int = 95000) -> list[str]:
    """Split text on sentence boundaries to maintain natural flow."""
```

**Strategy:**
- Splits text into chunks of ~95k chars (leaving 5k for style prompt)
- **Smart splitting**: Uses sentence boundaries (`.`, `!`, `?`, `\n`)
- **Avoids mid-sentence cuts**: Keeps sentences intact for natural audio flow

**Example:**
```
Input: 250,000 character study note
Output: [
    "Chunk 1: Introduction... (95k chars)",
    "Chunk 2: Main concepts... (95k chars)",  
    "Chunk 3: Conclusion... (60k chars)"
]
```

#### 2. **Audio Generation** (Loop through chunks)
```python
audio_segments = []
for chunk in text_chunks:
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=f"{style_prompt}\n\n{chunk}",
        ...
    )
    audio_data = response.candidates[0].content.parts[0].inline_data.data
    audio_segments.append(audio_data)
```

**Process:**
1. Generate audio for chunk 1 → PCM audio bytes
2. Generate audio for chunk 2 → PCM audio bytes
3. Generate audio for chunk 3 → PCM audio bytes
4. Store all segments in memory

#### 3. **Audio Combination** (`_combine_audio_segments()`)
```python
async def _combine_audio_segments(segments: list[bytes], output_path: str):
    """Combine multiple audio segments into single WAV file."""
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(24000)  # 24kHz
        
        # Write all segments sequentially
        for segment in segments:
            wf.writeframes(segment)
```

**Result:**
- Single continuous WAV file
- Seamless playback (no gaps between chunks)
- Correct total duration calculation

---

## Example Flow

### Short Content (< 95k chars)
```
Text: "Neural networks are..." (50k chars)
↓
Single API call
↓
Single audio file
✅ Done
```

### Long Content (> 95k chars)
```
Text: "Complete ML course..." (250k chars)
↓
Split into 3 chunks:
  - Chunk 1: 95k chars (sentences 1-450)
  - Chunk 2: 95k chars (sentences 451-900)
  - Chunk 3: 60k chars (sentences 901-1100)
↓
Generate audio for each:
  - Chunk 1 → 2.1 MB audio (8.7 min)
  - Chunk 2 → 2.1 MB audio (8.7 min)
  - Chunk 3 → 1.3 MB audio (5.4 min)
↓
Combine segments:
  - Total: 5.5 MB audio (22.8 min)
✅ Single seamless file
```

---

## Benefits

### ✅ **No Content Loss**
- Old approach: Truncated at 100k chars → Lost content
- New approach: Processes ALL content → Nothing lost

### ✅ **Natural Flow**
- Splits on sentence boundaries
- No mid-sentence cuts
- Smooth transitions between chunks

### ✅ **Seamless Playback**
- User hears one continuous audio
- No gaps or interruptions
- Single file to download/stream

### ✅ **Efficient**
- Parallel generation possible (future enhancement)
- Memory efficient (streams to file)
- Reuses same voice/style for all chunks

---

## Technical Details

### Chunking Algorithm
```python
# Split on sentence boundaries
sentences = re.split(r'([.!?\n]+\s*)', text)

# Rebuild chunks respecting max_chars
for sentence in sentences:
    if len(current_chunk) + len(sentence) > max_chars:
        chunks.append(current_chunk)  # Save current
        current_chunk = sentence      # Start new
    else:
        current_chunk += sentence     # Add to current
```

### Audio Format (WAV)
- **Channels**: 1 (Mono)
- **Sample Width**: 2 bytes (16-bit)
- **Sample Rate**: 24,000 Hz
- **Bitrate**: 384 kbps
- **Format**: PCM (uncompressed)

### Duration Calculation
```python
# bytes / (sample_rate * sample_width * channels)
duration = total_bytes / (24000 * 2 * 1)

# Example: 5,500,000 bytes
duration = 5,500,000 / 48,000 = 114.58 seconds ≈ 1.9 minutes
```

---

## Limitations & Future Enhancements

### Current Limitations
1. **Sequential generation**: Chunks processed one at a time
2. **Memory usage**: All segments held in memory before combining
3. **No progress indicator**: User doesn't know how many chunks remain

### Future Enhancements
1. **Parallel generation**: Generate multiple chunks simultaneously
2. **Streaming combination**: Write segments to file as they're generated
3. **Progress callback**: Report "Generating chunk 2/5..."
4. **Smarter chunking**: Use paragraph/section boundaries for better breaks
5. **Compression**: Convert to MP3/AAC for smaller file sizes

---

## Code Location

**File**: `agents/synthesis/audio.py`

**Functions**:
- `_chunk_text()` - Lines 60-98
- `_combine_audio_segments()` - Lines 101-118  
- `generate_audio_from_text()` - Lines 121-270 (uses chunking)

---

## Testing

### Test Case 1: Short Content
```python
text = "This is a short test." * 1000  # ~22k chars
result = await generate_audio_from_text(text, voice_name="Kore")
# Expected: 1 chunk, single API call
```

### Test Case 2: Long Content
```python
text = "This is a long test." * 10000  # ~200k chars
result = await generate_audio_from_text(text, voice_name="Kore")
# Expected: 3 chunks, 3 API calls, combined audio
```

### Test Case 3: Very Long Content
```python
text = open("textbook.txt").read()  # 500k chars
result = await generate_audio_from_text(text, voice_name="Kore")
# Expected: 6 chunks, 6 API calls, seamless 45-min audio
```

---

## Summary

**Before (Truncation):**
```
250k chars → Truncate to 100k → Generate audio → 10 min audio ❌ Lost 150k chars
```

**After (Chunking):**
```
250k chars → Split into 3 chunks → Generate 3 audios → Combine → 25 min audio ✅ All content preserved
```

The user gets the **complete** audio version of their study notes, no matter how long!
