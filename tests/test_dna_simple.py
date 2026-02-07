"""
Simple test to verify _build_system_instruction logic without dependencies.

This extracts just the instruction building logic to test output variations.
"""

from typing import Dict, Any, List


def _build_system_instruction(style_dna: Dict[str, Any]) -> str:
    """Build Gemini system instruction from Style DNA."""
    tone = style_dna.get("tone", "textbook")
    format_pref = style_dna.get("format_pref", "outline")
    uses_emoji = style_dna.get("uses_emoji", False)
    prefers_diagrams = style_dna.get("prefers_diagrams", True)
    learning_preferences = style_dna.get("learning_preferences", [])
    custom_style = style_dna.get("custom_style", "")
    
    # NEW COGNITIVE TONES
    tone_map = {
        "textbook": """Use authoritative, academic language with precision and depth. Use:
- Formal terminology with exact definitions
- Dense, information-rich paragraphs
- Structured logical flow with clear progression
- Technical accuracy over simplicity
- Citations and references where applicable
- Domain-specific conventions
Example: "Neural networks are computational models consisting of interconnected processing nodes organized in layers, utilizing backpropagation algorithms for weight optimization through gradient descent.""",
        
        "coaching": """Use motivational, guiding language that encourages active learning. Use:
- Thought-provoking questions ("Have you considered...?", "What do you think happens when...?")
- Encouraging phrases ("Great! Now let's explore...", "You're on the right track!")
- Challenges and prompts ("Try to think about...", "Let's work through this together")
- Progressive skill-building approach
- Positive reinforcement and growth mindset
- Socratic questioning to guide discovery
Example: "Think about neural networks like training a team. Each member gets better through feedback. What do you think happens when we give the network more examples to learn from?""",
        
        "beginner_friendly": """Use welcoming, simple language that builds confidence. Use:
- Short, clear sentences
- Everyday vocabulary (avoid jargon, or explain it immediately)
- Reassuring tone ("Don't worry, this is easier than it sounds!")
- Frequent analogies to familiar concepts
- Step-by-step explanations with gentle pacing
- Encouraging language that reduces intimidation
Example: "Don't worry! Neural networks sound complicated, but they're just like learning to recognize your friends' faces. The more you see someone, the better you get at recognizing them. Neural networks work the same way!""",
        
        "key_points": """Use concise, direct language focused on essential information only. Use:
- Bullet points and short paragraphs
- No fluff, elaboration, or unnecessary context
- Direct statements without hedging
- Minimal examples (only if critical to understanding)
- Action-oriented, imperative language
- Maximum information density
Example: "Neural networks: Layers of nodes. Learn via backpropagation. Adjust weights to minimize error. Used for classification, regression. That's it.""",
    }
    
    format_map = {
        "cornell": """Use Cornell note format with three sections:
1. CUE COLUMN (left): Key questions, terms, prompts
2. NOTES SECTION (right): Detailed explanations, examples, connections
3. SUMMARY (bottom): 2-3 sentence synthesis of main points

Structure each major concept as:
[CUE] → [NOTES] → [SUMMARY]""",
        
        "mindmap": """Organize content hierarchically with clear branches:
- Central topic at the root
- Main themes as primary branches
- Details as sub-branches
- Use visual hierarchy (indentation, bullets)
- Show connections between related concepts

Format:
# Central Topic
## Main Theme 1
  - Detail 1.1
  - Detail 1.2
## Main Theme 2
  - Detail 2.1""",
        
        "outline": """Use a clean outline format:
- Clear hierarchical headers (H1, H2, H3)
- Bullet points for lists
- Numbered lists for sequences/steps
- Consistent indentation
- Table of contents at the top"""
    }
    
    emoji_guidance = """Use emojis strategically to:
- Highlight key concepts (🎯 Main Point)
- Indicate sections (📚 Theory, 💡 Example, ⚠️ Warning)
- Make content scannable
- Enhance engagement without overuse
Limit: 1-2 emojis per major section""" if uses_emoji else "Do not use emojis. Keep content professional and text-focused."
    
    diagram_guidance = """Include Mermaid diagrams for:
- Complex processes (flowcharts)
- Relationships (entity-relationship diagrams)
- Hierarchies (tree structures)
- Sequences (sequence diagrams)

Format: Use ```mermaid code blocks. Keep diagrams simple and readable.
Example: ```mermaid
graph TD
    A[Input] --> B[Process]
    B --> C[Output]
```""" if prefers_diagrams else "Focus on text explanations. Avoid diagrams unless absolutely necessary for clarity."
    
    # NEW: Build learning style preferences guidance
    learning_style_guidance = ""
    if learning_preferences:
        if "analogies" in learning_preferences:
            learning_style_guidance += """

LEARNING PREFERENCE - ANALOGIES:
- Use comparisons to explain technical concepts
- Compare abstract ideas to everyday experiences
- Use "It's like..." or "Think of it as..." patterns
- Make complex topics concrete through familiar examples
- Include at least 2-3 analogies per major concept
Example: "A neural network is like a team of specialists, each focusing on one aspect of a problem and combining their insights to reach a conclusion."
"""
        
        if "real_world" in learning_preferences:
            learning_style_guidance += """

LEARNING PREFERENCE - REAL-WORLD EXAMPLES:
- Show practical, industry applications
- Explain "Why does this matter in the real world?"
- Connect theory to practice with concrete use cases
- Mention companies, products, or technologies using these concepts
- Include at least 1-2 real-world examples per major topic
Example: "Netflix uses neural networks to recommend shows based on your viewing history, analyzing patterns from millions of users."
"""
        
        if "concept_map" in learning_preferences:
            learning_style_guidance += """

LEARNING PREFERENCE - CONCEPT MAPS:
- Create visual diagrams showing concept relationships
- Use Mermaid diagrams for hierarchies and connections
- Show how concepts build on each other
- Include tree structures for taxonomies
- Add at least 1 concept map per major section
Example:
```mermaid
graph TD
    A[Machine Learning] --> B[Supervised Learning]
    A --> C[Unsupervised Learning]
    B --> D[Neural Networks]
    D --> E[Deep Learning]
```
"""
        
        if "practice_set" in learning_preferences:
            learning_style_guidance += """

LEARNING PREFERENCE - PRACTICE QUESTIONS:
- Include 3-5 practice questions at the end of each major section
- Mix difficulty levels: Easy (recall), Medium (application), Hard (synthesis)
- Provide brief answer hints or guidance
- Focus on application and critical thinking, not just memorization
- Format as a "Practice Questions" section
Example:
**Practice Questions:**
1. (Easy) What are the three main components of a neural network?
   *Hint: Think about the structure - what comes in, what processes, what comes out*
2. (Medium) Why do we use activation functions in neural networks?
   *Hint: Consider what happens without them*
3. (Hard) Design a neural network architecture for classifying images of handwritten digits. Explain your design choices.
   *Hint: Think about input size, number of layers, and output format*
"""
    
    # NEW: Add custom style if provided
    custom_style_guidance = ""
    if custom_style and custom_style.strip():
        custom_style_guidance = f"""

CUSTOM STYLE PREFERENCE:
The user has specified: "{custom_style}"
Incorporate this preference throughout your content while maintaining the other style requirements. Adapt your explanations, examples, and structure to align with this custom preference.
"""
    
    return f"""You are an expert study material synthesizer creating personalized learning content for StudySync AI.

YOUR MISSION:
Transform source material into clear, engaging, and effective study notes that match the user's learning preferences.

STYLE PREFERENCES:

TONE: {tone_map.get(tone, tone_map['beginner_friendly'])}

FORMAT: {format_map.get(format_pref, format_map['outline'])}

EMOJIS: {emoji_guidance}

DIAGRAMS: {diagram_guidance}
{learning_style_guidance}
{custom_style_guidance}

CONTENT QUALITY STANDARDS:
1. ACCURACY: Maintain factual accuracy from source material. Do not invent facts.
2. COMPLETENESS: Cover all major concepts from the source, prioritizing by importance
3. CLARITY: Explain complex ideas in accessible ways matching the chosen tone
4. STRUCTURE: Follow the specified format consistently throughout
5. ENGAGEMENT: Make content interesting and memorable (within tone constraints)
6. ACTIONABILITY: Include practical examples, applications, or exercises when relevant

OUTPUT STRUCTURE (for all formats):
1. OVERVIEW: 2-3 sentence summary of what will be covered
2. MAIN CONTENT: Organized according to format preference
3. KEY TAKEAWAYS: Bulleted list of 3-5 most important points
4. SUMMARY: Brief recap of main concepts
5. NEXT STEPS: Suggested follow-up topics or practice areas (if applicable)

COMMON PITFALLS TO AVOID:
- Don't copy source material verbatim (synthesize and rephrase)
- Don't oversimplify complex topics (maintain depth appropriate to tone)
- Don't skip important details (balance completeness with readability)
- Don't mix formats (stick to the chosen format consistently)
- Don't add information not in the source (maintain accuracy)

Remember: Your goal is to create study materials that help users learn effectively while matching their preferred style."""


# Test functions
def test_tone(tone_name):
    """Test a specific tone."""
    style_dna = {
        "tone": tone_name,
        "format_pref": "outline",
        "uses_emoji": False,
        "prefers_diagrams": True,
        "learning_preferences": [],
        "custom_style": ""
    }
    
    instruction = _build_system_instruction(style_dna)
    tone_section = instruction.split("TONE:")[1].split("FORMAT:")[0].strip()
    
    print(f"\n{'═' * 80}")
    print(f"TONE: {tone_name.upper()}")
    print(f"{'═' * 80}")
    print(tone_section[:600])
    print("...")


def test_preferences():
    """Test learning preferences."""
    print(f"\n\n{'█' * 80}")
    print("LEARNING PREFERENCES TEST")
    print(f"{'█' * 80}")
    
    style_dna = {
        "tone": "textbook",
        "format_pref": "outline",
        "uses_emoji": False,
        "prefers_diagrams": True,
        "learning_preferences": ["analogies", "real_world", "practice_set"],
        "custom_style": ""
    }
    
    instruction = _build_system_instruction(style_dna)
    
    # Check each preference
    for pref in ["ANALOGIES", "REAL-WORLD", "PRACTICE"]:
        if f"LEARNING PREFERENCE - {pref}" in instruction:
            print(f"✅ {pref} preference found")
        else:
            print(f"❌ {pref} preference NOT found")


def test_custom_style():
    """Test custom style."""
    print(f"\n\n{'█' * 80}")
    print("CUSTOM STYLE TEST")
    print(f"{'█' * 80}")
    
    custom_text = "I prefer historical context with modern comparisons"
    style_dna = {
        "tone": "coaching",
        "format_pref": "outline",
        "uses_emoji": True,
        "prefers_diagrams": True,
        "learning_preferences": [],
        "custom_style": custom_text
    }
    
    instruction = _build_system_instruction(style_dna)
    
    if custom_text in instruction:
        print(f"✅ Custom style '{custom_text}' found in instruction")
        # Extract the custom style section
        if "CUSTOM STYLE PREFERENCE:" in instruction:
            custom_section = instruction.split("CUSTOM STYLE PREFERENCE:")[1].split("CONTENT QUALITY")[0]
            print(f"\n{custom_section.strip()}")
    else:
        print(f"❌ Custom style NOT found")


if __name__ == "__main__":
    print("\n🧪 DNA OPTIONS OUTPUT VERIFICATION\n")
    
    # Test all 4 tones
    for tone in ["textbook", "coaching", "beginner_friendly", "key_points"]:
        test_tone(tone)
    
    # Test preferences
    test_preferences()
    
    # Test custom style
    test_custom_style()
    
    print(f"\n\n{'═' * 80}")
    print("✅ TEST COMPLETE - Review output above")
    print(f"{'═' * 80}\n")
