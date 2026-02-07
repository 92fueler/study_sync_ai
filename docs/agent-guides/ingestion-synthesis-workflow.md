# How Ingestion and Synthesis Agents Work Together

## 🎯 The Big Picture

**Ingestion Agent** and **Synthesis Agent** work in a **producer-consumer relationship**:

- **Ingestion** = The **Producer** (prepares raw ingredients)
- **Synthesis** = The **Consumer** (cooks the meal)

They **don't call each other directly** - they communicate through the **database**!

---

## 🔄 The Complete Workflow

### User Uploads a PDF

```
┌─────────────────────────────────────────────────────────────┐
│                    USER UPLOADS PDF                         │
│                "machine_learning.pdf"                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   GATEWAY RECEIVES FILE                     │
│         POST /api/v1/upload (user_id, file)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              STEP 1: INGESTION AGENT                        │
│                                                             │
│  1. Parse PDF → Extract text                               │
│  2. Extract topics: ["Neural Networks", "Backprop"]        │
│  3. Generate embeddings (vector: [0.123, 0.456, ...])      │
│  4. Store in database:                                      │
│     ┌──────────────────────────────────────┐               │
│     │ content_items table:                 │               │
│     │ - id: "abc-123"                      │               │
│     │ - raw_text: "Neural networks are..." │               │
│     │ - topics: ["Neural Networks", ...]   │               │
│     │ - embedding: [0.123, 0.456, ...]     │               │
│     │ - word_count: 5000                   │               │
│     └──────────────────────────────────────┘               │
│                                                             │
│  5. Returns: {"content_id": "abc-123"}                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            STEP 2: ORCHESTRATOR TRIGGERED                   │
│                                                             │
│  Gateway calls Orchestrator:                                │
│  "New content uploaded: abc-123"                            │
│                                                             │
│  Orchestrator calls: schedule_generation(                   │
│    user_id="user_123",                                      │
│    job_type="generate_5min_new",                            │
│    content_id="abc-123"                                     │
│  )                                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              STEP 3: SYNTHESIS AGENT                        │
│                                                             │
│  Orchestrator calls Synthesis via HTTP:                     │
│  POST http://synthesis-agent:8003/run_sse                   │
│                                                             │
│  Synthesis Agent:                                           │
│  1. Reads from database:                                    │
│     SELECT raw_text FROM content_items                      │
│     WHERE id = 'abc-123'                                    │
│     → Gets: "Neural networks are..."                        │
│                                                             │
│  2. Reads user's Style DNA from database:                   │
│     SELECT study_preferences FROM user_settings             │
│     WHERE user_id = 'user_123'                              │
│     → Gets: {"tone": "coaching", "format": "outline"}       │
│                                                             │
│  3. Builds personalized prompt:                             │
│     "You are a coach. Use outline format.                   │
│      Create 5-min summary of: [raw_text]"                   │
│                                                             │
│  4. Calls Gemini API:                                       │
│     response = gemini.generate_content(prompt)              │
│     → Gets personalized summary                             │
│                                                             │
│  5. Stores artifact in database:                            │
│     ┌──────────────────────────────────────┐               │
│     │ artifacts table:                     │               │
│     │ - id: "art-789"                      │               │
│     │ - user_id: "user_123"                │               │
│     │ - content_ids: ["abc-123"]           │               │
│     │ - artifact_type: "5min"              │               │
│     │ - content: "# ML Summary\n\n..."     │               │
│     │ - estimated_minutes: 5               │               │
│     └──────────────────────────────────────┘               │
│                                                             │
│  6. Returns: {"artifact_id": "art-789"}                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 STEP 4: USER NOTIFICATION                   │
│                                                             │
│  Orchestrator creates notification:                         │
│  "Your 5-minute summary is ready! 📚"                       │
│                                                             │
│  User clicks → Frontend fetches artifact from database      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database as the Bridge

The key insight: **Ingestion writes, Synthesis reads** from the same database tables.

### What Ingestion Writes:

```sql
-- content_items table
INSERT INTO content_items (
    id,           -- "abc-123"
    raw_text,     -- Full extracted text
    topics,       -- ["Neural Networks", "Backpropagation"]
    embedding,    -- Vector for semantic search
    word_count,   -- 5000
    media_type    -- "application/pdf"
)
```

### What Synthesis Reads:

```sql
-- Synthesis queries the same table
SELECT raw_text, topics 
FROM content_items 
WHERE id = 'abc-123'

-- Also reads user preferences
SELECT study_preferences 
FROM user_settings 
WHERE user_id = 'user_123'
```

### What Synthesis Writes:

```sql
-- artifacts table
INSERT INTO artifacts (
    id,              -- "art-789"
    user_id,         -- "user_123"
    content_ids,     -- ["abc-123"] (references Ingestion's content)
    artifact_type,   -- "5min"
    content,         -- Generated personalized summary
    estimated_minutes -- 5
)
```

---

## 🔗 The Data Flow

### 1. Ingestion → Database

```python
# agents/ingestion/tools.py

async def ingest_content(...):
    # Parse PDF
    content_text = extract_text_from_pdf(file)
    
    # Extract topics using Gemini
    topics = await extract_topics(content_text)
    # → ["Neural Networks", "Gradient Descent"]
    
    # Generate embeddings
    embedding = await generate_embedding(content_text)
    # → [0.123, 0.456, 0.789, ...]
    
    # WRITE TO DATABASE
    row = await conn.fetchrow(
        """
        INSERT INTO content_items 
        (content_hash, title, raw_text, topics, embedding, word_count)
        VALUES ($1, $2, $3, $4, $5::vector, $6)
        RETURNING id
        """,
        content_hash, filename, content_text, 
        json.dumps(topics), embedding_str, word_count
    )
    
    content_id = str(row["id"])  # "abc-123"
    
    return {"content_id": content_id, "topics": topics}
```

### 2. Database → Synthesis

```python
# agents/synthesis/tools.py

async def generate_5min_summary(user_id, content_id, ...):
    # READ FROM DATABASE (what Ingestion wrote)
    row = await conn.fetchrow(
        "SELECT raw_text FROM content_items WHERE id = $1", 
        content_id
    )
    
    source_text = row["raw_text"]  # The text Ingestion extracted
    
    # Also read user preferences
    prefs = await conn.fetchrow(
        "SELECT study_preferences FROM user_settings WHERE user_id = $1",
        user_id
    )
    
    style_dna = prefs["study_preferences"]
    # → {"tone": "coaching", "format": "outline"}
    
    # Generate personalized content
    prompt = build_prompt(source_text, style_dna)
    response = gemini.generate_content(prompt)
    
    # WRITE TO DATABASE (new artifact)
    artifact_row = await conn.fetchrow(
        """
        INSERT INTO artifacts 
        (user_id, content_ids, artifact_type, content, estimated_minutes)
        VALUES ($1, $2, '5min', $3, 5)
        RETURNING id
        """,
        user_id, [content_id], response.text
    )
    
    return {"artifact_id": str(artifact_row["id"])}
```

---

## 📊 Key Tables

### `content_items` (Ingestion's Output)

| Column | Type | Description | Written By |
|--------|------|-------------|------------|
| `id` | UUID | Content identifier | Ingestion |
| `raw_text` | TEXT | Extracted text | Ingestion |
| `topics` | JSONB | Extracted topics | Ingestion |
| `embedding` | VECTOR | Semantic embedding | Ingestion |
| `word_count` | INT | Word count | Ingestion |
| `media_type` | TEXT | File type | Ingestion |

### `artifacts` (Synthesis's Output)

| Column | Type | Description | Written By |
|--------|------|-------------|------------|
| `id` | UUID | Artifact identifier | Synthesis |
| `user_id` | UUID | User who owns it | Synthesis |
| `content_ids` | UUID[] | Source content IDs | Synthesis (references Ingestion) |
| `artifact_type` | TEXT | "5min", "full", etc. | Synthesis |
| `content` | TEXT | Generated content | Synthesis |
| `estimated_minutes` | INT | Reading time | Synthesis |
| `profile_version` | INT | DNA version used | Synthesis |

### The Link:

```
content_items.id  ←→  artifacts.content_ids
     (Ingestion)           (Synthesis)
```

---

## 🎨 Detailed Example

### User uploads "neural_networks.pdf"

**Step 1: Ingestion Agent**

```python
# Input: PDF file
file_content = b"%PDF-1.4\n..."

# Extract text
raw_text = """
Neural networks are computational models inspired by biological 
neural systems. They consist of interconnected nodes (neurons) 
organized in layers. The network learns by adjusting weights 
through backpropagation...
"""

# Extract topics
topics = ["Neural Networks", "Backpropagation", "Gradient Descent"]

# Generate embedding
embedding = [0.123, 0.456, 0.789, ...]  # 768 dimensions

# Store in database
INSERT INTO content_items VALUES (
    id: "abc-123",
    raw_text: "Neural networks are...",
    topics: ["Neural Networks", "Backpropagation", "Gradient Descent"],
    embedding: [0.123, 0.456, ...],
    word_count: 5000
)

# Return
{"content_id": "abc-123"}
```

**Step 2: Orchestrator Triggers Synthesis**

```python
# Orchestrator calls Synthesis Agent
POST http://synthesis-agent:8003/run_sse
Body: {
    "new_message": {
        "text": "Generate 5-min summary for content_id: abc-123, user_id: user_123"
    }
}
```

**Step 3: Synthesis Agent**

```python
# Read what Ingestion wrote
SELECT raw_text FROM content_items WHERE id = 'abc-123'
→ "Neural networks are computational models..."

# Read user preferences
SELECT study_preferences FROM user_settings WHERE user_id = 'user_123'
→ {"tone": "coaching", "format": "outline"}

# Build personalized prompt
prompt = """
You are a coach. Use outline format.

Create a 5-minute summary of:
Neural networks are computational models inspired by biological 
neural systems. They consist of interconnected nodes (neurons)...
"""

# Call Gemini
response = gemini.generate_content(prompt)
→ """
# Neural Networks: Your Quick Guide

## What Are They?
Think of neural networks like a team of decision-makers...

## How Do They Learn?
Great question! They learn through a process called backpropagation...

## Key Takeaways
• Neural networks mimic how your brain works
• They learn from examples by adjusting connections
• Backpropagation is the learning algorithm
"""

# Store artifact
INSERT INTO artifacts VALUES (
    id: "art-789",
    user_id: "user_123",
    content_ids: ["abc-123"],  # ← Links back to Ingestion's content
    artifact_type: "5min",
    content: "# Neural Networks: Your Quick Guide...",
    estimated_minutes: 5
)

# Return
{"artifact_id": "art-789"}
```

---

## 🔑 Key Insights

### 1. **No Direct Communication**

Ingestion and Synthesis **never call each other**:
- ❌ Ingestion doesn't call Synthesis
- ❌ Synthesis doesn't call Ingestion
- ✅ They communicate through the **database**

### 2. **Orchestrator is the Coordinator**

```
Ingestion ← Gateway → Orchestrator → Synthesis
    ↓                                     ↓
Database ←────────────────────────────────┘
```

### 3. **Separation of Concerns**

| Agent | Responsibility |
|-------|----------------|
| **Ingestion** | Parse files, extract metadata, create embeddings |
| **Synthesis** | Generate personalized content from raw text |
| **Orchestrator** | Coordinate the workflow |

### 4. **Content IDs Link Them**

```python
# Ingestion creates content
content_id = "abc-123"

# Synthesis references it
artifacts.content_ids = ["abc-123"]

# This creates the relationship:
# "This artifact was generated from this content"
```

---

## 🚀 Why This Design?

### ✅ **Advantages:**

1. **Loose Coupling**
   - Agents can be updated independently
   - Ingestion doesn't need to know about Synthesis

2. **Scalability**
   - Can run multiple Synthesis agents in parallel
   - Database handles concurrency

3. **Reliability**
   - If Synthesis fails, content is still in database
   - Can retry generation without re-ingesting

4. **Flexibility**
   - Can generate multiple artifacts from same content
   - Can regenerate with different Style DNA

### ⚠️ **Trade-offs:**

1. **Database Dependency**
   - Both agents need database access
   - Database becomes single point of failure

2. **No Real-time Streaming**
   - Can't stream from Ingestion → Synthesis
   - Must wait for Ingestion to complete

---

## 💡 Common Scenarios

### Scenario 1: Regenerate with New DNA

```python
# User changes cognitive tone from "eli5" to "academic"
# Content is already ingested (content_id = "abc-123")

# Just call Synthesis again with new DNA
generate_5min_summary(
    user_id="user_123",
    content_id="abc-123",  # Same content!
    profile_version=2,      # New DNA version
    style_dna={"tone": "academic", ...}
)

# Synthesis reads same raw_text, generates new artifact
# No need to re-ingest!
```

### Scenario 2: Multiple Artifacts from Same Content

```python
# Ingestion creates: content_id = "abc-123"

# Generate 5-min summary
artifact_1 = generate_5min_summary(content_id="abc-123")
# → artifact_id = "art-789"

# Generate full notes
artifact_2 = generate_artifact(content_ids=["abc-123"], time=25)
# → artifact_id = "art-790"

# Both reference same content:
# artifacts.content_ids = ["abc-123"]
```

### Scenario 3: Combine Multiple Contents

```python
# User uploads 3 PDFs
# Ingestion creates:
# - content_id = "abc-123" (Chapter 1)
# - content_id = "abc-124" (Chapter 2)
# - content_id = "abc-125" (Chapter 3)

# Synthesis can combine them:
generate_artifact(
    content_ids=["abc-123", "abc-124", "abc-125"],
    time=60
)

# Synthesis reads all 3 raw_texts, creates unified summary
```

---

## 📝 Summary

**Ingestion and Synthesis work together through the database:**

1. **Ingestion** extracts and stores raw content
2. **Orchestrator** triggers Synthesis when needed
3. **Synthesis** reads raw content and generates personalized artifacts
4. **Database** is the bridge connecting them

**Key relationship:**
```
content_items.id (Ingestion) ←→ artifacts.content_ids (Synthesis)
```

This design allows flexible, scalable, and reliable content generation! 🎉
