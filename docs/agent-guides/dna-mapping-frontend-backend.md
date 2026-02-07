# DNA Options Mapping: Frontend ↔ Backend

## 🔍 The Confusion: Two Different Concepts

You're mixing two separate DNA concepts:

### 1️⃣ **Preferred Content Formats** (What media types you want)
- 🎧 Audio
- 📹 Video  
- 📝 Notes
- 🖼️ Image

### 2️⃣ **Note Format Preference** (How notes are structured)
- 📋 Outline
- 📓 Cornell
- 🗺️ Mind Map

---

## 📊 Complete Frontend DNA Options

Looking at your `Onboarding.tsx`, here's what users can configure:

### **Section 1: Preferred Content Formats** (Lines 100-104)
```typescript
{ id: 'audio', label: 'Audio', icon: Headphones, desc: 'Listening' },
{ id: 'video', label: 'Video', icon: Video, desc: 'Watching' },
{ id: 'notes', label: 'Notes', icon: FileText, desc: 'Reading' },
{ id: 'image', label: 'Image', icon: ImageIcon, desc: 'Visuals' },
```

**What this means:** "I want to receive study materials as audio/video/notes/images"

**Current status:** ⚠️ Only **Notes** are actually generated (see `docs/supported-formats.md`)

---

### **Section 2: Learning Style Preferences** (Lines 139-143)
```typescript
{ id: 'analogies', label: 'Analogies', icon: '🧩', description: 'Explain it using comparisons' },
{ id: 'real_world', label: 'Real-World Examples', icon: '🌍', description: 'Show me how it applies to industry' },
{ id: 'concept_map', label: 'Concept Map', icon: '🗺️', description: 'Visualize the structure' },
{ id: 'practice_set', label: 'Practice Set', icon: '✅', description: 'Give me questions to test myself' },
```

**What this means:** "When creating notes, include analogies/real-world examples/concept maps/practice questions"

**Current status:** ✅ **Fully implemented** in our recent changes

---

### **Section 3: Custom Style** (Lines 176-182)
```typescript
<input
    type="text"
    value={customStyle}
    onChange={(e) => setCustomStyle(e.target.value)}
    placeholder="e.g., 'I prefer detailed historical context with modern-day comparisons.'"
/>
```

**What this means:** Free-text description of your learning style

**Current status:** ✅ **Fully implemented**

---

### **Section 4: Cognitive Tone** (Lines 187-249)
```typescript
{ tone: 'textbook', label: '🎓 Textbook', desc: 'Authoritative, dense, precise' },
{ tone: 'coaching', label: '📣 Coaching', desc: 'Motivational, probing, guides you' },
{ tone: 'beginner_friendly', label: '🌱 Beginner Friendly', desc: 'Welcoming, simple, reassuring' },
{ tone: 'key_points', label: '⚡️ Key Points Only', desc: 'Blunt, efficient, strictly business' },
```

**What this means:** "Use this communication style when writing"

**Current status:** ✅ **Fully implemented**

---

## ❓ Where is Cornell Format?

**Cornell is NOT in the frontend DNA page!** It's a **backend-only option** currently.

### Backend Format Options (in `agents/synthesis/tools.py`)
```python
format_map = {
    "cornell": "Use Cornell note format...",
    "mindmap": "Organize content hierarchically...",
    "outline": "Use a clean outline format..."
}
```

### Frontend DNA Page Options
- ❌ No format selector visible
- ✅ Only has: Content Formats, Learning Preferences, Custom Style, Cognitive Tone

---

## 🎯 How They Map Together

### Frontend Saves (from `Onboarding.tsx` line 268-273):
```typescript
study_preferences: {
    formats: selectedFormats,           // ['audio', 'video', 'notes', 'image']
    preferences: selectedPreferences,   // ['analogies', 'real_world', 'concept_map', 'practice_set']
    custom_style: customStyle,          // "I prefer historical context..."
    cognitive_tone: cognitiveTone,      // 'textbook' | 'coaching' | 'beginner_friendly' | 'key_points'
}
```

### Backend Expects (in `StyleDNA` model):
```python
class StyleDNA(BaseModel):
    format_pref: str = "outline"                    # ❌ NOT in frontend!
    tone: str = "textbook"                          # ✅ Maps to cognitive_tone
    uses_emoji: bool = False                        # ❌ NOT in frontend!
    prefers_diagrams: bool = True                   # ❌ NOT in frontend!
    learning_preferences: List[str] = []            # ✅ Maps to preferences
    custom_style: str = ""                          # ✅ Maps to custom_style
```

---

## 🚨 **The Mismatch Problem**

### What Frontend Sends:
```json
{
  "formats": ["notes", "audio"],
  "preferences": ["analogies", "real_world"],
  "custom_style": "I prefer historical context",
  "cognitive_tone": "coaching"
}
```

### What Backend Expects:
```json
{
  "format_pref": "outline",
  "tone": "coaching",
  "uses_emoji": false,
  "prefers_diagrams": true,
  "learning_preferences": ["analogies", "real_world"],
  "custom_style": "I prefer historical context"
}
```

### Missing Mappings:
1. ❌ `formats` → Not used by Synthesis Agent (only determines what to generate)
2. ❌ `format_pref` → Not exposed in frontend (defaults to "outline")
3. ❌ `uses_emoji` → Not exposed in frontend (defaults to false)
4. ❌ `prefers_diagrams` → Not exposed in frontend (defaults to true)

---

## 💡 Solution: Add Missing Options to Frontend

### Option 1: Add Note Format Selector
```typescript
// Add to Onboarding.tsx after Cognitive Tone section
<div className="mb-8">
    <h2 className="text-xl font-semibold text-gray-900 mb-4">Note Format</h2>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <button onClick={() => setFormatPref('outline')}>
            📋 Outline
            <p className="text-xs">Clean hierarchical structure</p>
        </button>
        <button onClick={() => setFormatPref('cornell')}>
            📓 Cornell Notes
            <p className="text-xs">Cue column + notes + summary</p>
        </button>
        <button onClick={() => setFormatPref('mindmap')}>
            🗺️ Mind Map
            <p className="text-xs">Visual concept hierarchy</p>
        </button>
    </div>
</div>
```

### Option 2: Add Emoji & Diagram Toggles
```typescript
<div className="flex gap-4 mb-6">
    <label className="flex items-center gap-2">
        <input 
            type="checkbox" 
            checked={usesEmoji}
            onChange={(e) => setUsesEmoji(e.target.checked)}
        />
        Use emojis in notes 😊
    </label>
    
    <label className="flex items-center gap-2">
        <input 
            type="checkbox" 
            checked={prefersDiagrams}
            onChange={(e) => setPrefersDiagrams(e.target.checked)}
        />
        Include diagrams 📊
    </label>
</div>
```

---

## 📝 Updated Test to Match Frontend

Let me update the test to use the actual frontend values:

```python
# Test with ACTUAL frontend DNA options
def test_frontend_dna():
    """Test with values that come from the frontend."""
    
    # This is what the frontend sends
    frontend_data = {
        "formats": ["notes", "audio"],                    # Content formats (not used by synthesis yet)
        "preferences": ["analogies", "real_world"],       # Learning preferences ✅
        "custom_style": "I prefer historical context",    # Custom style ✅
        "cognitive_tone": "coaching"                      # Cognitive tone ✅
    }
    
    # This is what we need to transform it to for the backend
    style_dna = {
        "tone": frontend_data["cognitive_tone"],          # coaching
        "format_pref": "outline",                         # Default (not in frontend)
        "uses_emoji": False,                              # Default (not in frontend)
        "prefers_diagrams": True,                         # Default (not in frontend)
        "learning_preferences": frontend_data["preferences"],  # ["analogies", "real_world"]
        "custom_style": frontend_data["custom_style"]     # "I prefer historical context"
    }
    
    instruction = _build_system_instruction(style_dna)
    
    # Verify it works
    assert "coaching" in instruction.lower() or "motivational" in instruction.lower()
    assert "ANALOGIES" in instruction
    assert "REAL-WORLD" in instruction
    assert "historical context" in instruction
```

---

## ✅ Summary

### What's in Frontend DNA Page:
1. ✅ **Preferred Content Formats** (audio, video, notes, image)
2. ✅ **Learning Style Preferences** (analogies, real_world, concept_map, practice_set)
3. ✅ **Custom Style** (free text)
4. ✅ **Cognitive Tone** (textbook, coaching, beginner_friendly, key_points)

### What's Missing from Frontend:
1. ❌ **Note Format** (outline, cornell, mindmap) - Defaults to "outline"
2. ❌ **Use Emojis** toggle - Defaults to false
3. ❌ **Include Diagrams** toggle - Defaults to true

### Cornell Format:
- **Backend:** ✅ Implemented in `format_map`
- **Frontend:** ❌ Not exposed to users
- **Default:** Uses "outline" format instead

**To use Cornell format:** You'd need to add a format selector to the frontend!
