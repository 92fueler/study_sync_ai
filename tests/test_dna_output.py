"""
Test script to verify new DNA options produce different outputs.

This script tests:
1. All 4 new cognitive tones (textbook, coaching, beginner_friendly, key_points)
2. Learning preferences (analogies, real_world, concept_map, practice_set)
3. Custom style integration

Run: python tests/test_dna_output.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.synthesis.tools import _build_system_instruction


def test_cognitive_tones():
    """Test that each cognitive tone produces distinct instructions."""
    print("=" * 80)
    print("TESTING COGNITIVE TONES")
    print("=" * 80)
    
    tones = ["textbook", "coaching", "beginner_friendly", "key_points"]
    
    for tone in tones:
        style_dna = {
            "tone": tone,
            "format_pref": "outline",
            "uses_emoji": False,
            "prefers_diagrams": True,
            "learning_preferences": [],
            "custom_style": ""
        }
        
        instruction = _build_system_instruction(style_dna)
        
        print(f"\n{'─' * 80}")
        print(f"TONE: {tone.upper()}")
        print(f"{'─' * 80}")
        
        # Extract just the TONE section from the instruction
        tone_section = instruction.split("TONE:")[1].split("FORMAT:")[0].strip()
        print(tone_section[:500] + "..." if len(tone_section) > 500 else tone_section)
        print()


def test_learning_preferences():
    """Test that learning preferences add appropriate guidance."""
    print("\n" + "=" * 80)
    print("TESTING LEARNING PREFERENCES")
    print("=" * 80)
    
    preferences = ["analogies", "real_world", "concept_map", "practice_set"]
    
    for pref in preferences:
        style_dna = {
            "tone": "textbook",
            "format_pref": "outline",
            "uses_emoji": False,
            "prefers_diagrams": True,
            "learning_preferences": [pref],
            "custom_style": ""
        }
        
        instruction = _build_system_instruction(style_dna)
        
        print(f"\n{'─' * 80}")
        print(f"LEARNING PREFERENCE: {pref.upper()}")
        print(f"{'─' * 80}")
        
        # Check if the preference guidance is included
        if f"LEARNING PREFERENCE - {pref.upper().replace('_', '-')}" in instruction:
            # Extract the preference section
            pref_section = instruction.split(f"LEARNING PREFERENCE - {pref.upper().replace('_', '-')}:")[1]
            # Get until the next section or end
            end_markers = ["LEARNING PREFERENCE", "CUSTOM STYLE", "CONTENT QUALITY"]
            for marker in end_markers:
                if marker in pref_section:
                    pref_section = pref_section.split(marker)[0]
                    break
            print(pref_section.strip()[:400] + "..." if len(pref_section.strip()) > 400 else pref_section.strip())
        else:
            print("❌ PREFERENCE NOT FOUND IN INSTRUCTION")
        print()


def test_custom_style():
    """Test that custom style is integrated."""
    print("\n" + "=" * 80)
    print("TESTING CUSTOM STYLE")
    print("=" * 80)
    
    style_dna = {
        "tone": "textbook",
        "format_pref": "outline",
        "uses_emoji": False,
        "prefers_diagrams": True,
        "learning_preferences": [],
        "custom_style": "I prefer detailed historical context with modern-day comparisons"
    }
    
    instruction = _build_system_instruction(style_dna)
    
    print(f"\n{'─' * 80}")
    print(f"CUSTOM STYLE: {style_dna['custom_style']}")
    print(f"{'─' * 80}")
    
    if "CUSTOM STYLE PREFERENCE" in instruction:
        custom_section = instruction.split("CUSTOM STYLE PREFERENCE:")[1]
        # Get until the next section
        if "CONTENT QUALITY" in custom_section:
            custom_section = custom_section.split("CONTENT QUALITY")[0]
        print(custom_section.strip())
    else:
        print("❌ CUSTOM STYLE NOT FOUND IN INSTRUCTION")
    print()


def test_combined():
    """Test combination of tone + preferences + custom style."""
    print("\n" + "=" * 80)
    print("TESTING COMBINED: Coaching Tone + All Preferences + Custom Style")
    print("=" * 80)
    
    style_dna = {
        "tone": "coaching",
        "format_pref": "outline",
        "uses_emoji": True,
        "prefers_diagrams": True,
        "learning_preferences": ["analogies", "real_world", "practice_set"],
        "custom_style": "I learn best with historical context and step-by-step examples"
    }
    
    instruction = _build_system_instruction(style_dna)
    
    print(f"\n{'─' * 80}")
    print("FULL INSTRUCTION LENGTH:", len(instruction), "characters")
    print(f"{'─' * 80}")
    
    # Check all components are present
    checks = {
        "Coaching tone": "motivational" in instruction.lower() or "coaching" in instruction.lower(),
        "Analogies preference": "LEARNING PREFERENCE - ANALOGIES" in instruction,
        "Real-world preference": "LEARNING PREFERENCE - REAL-WORLD" in instruction,
        "Practice set preference": "LEARNING PREFERENCE - PRACTICE" in instruction,
        "Custom style": "historical context" in instruction.lower(),
        "Emoji guidance": "emoji" in instruction.lower(),
        "Diagram guidance": "mermaid" in instruction.lower()
    }
    
    print("\nComponent Checks:")
    for component, present in checks.items():
        status = "✅" if present else "❌"
        print(f"  {status} {component}")
    
    print(f"\n{'─' * 80}")
    print("SAMPLE OUTPUT (first 1000 chars):")
    print(f"{'─' * 80}")
    print(instruction[:1000] + "...")


def test_legacy_tones():
    """Test that legacy tones still work."""
    print("\n" + "=" * 80)
    print("TESTING LEGACY TONE COMPATIBILITY")
    print("=" * 80)
    
    legacy_tones = ["eli5", "socratic", "academic"]
    
    for tone in legacy_tones:
        style_dna = {
            "tone": tone,
            "format_pref": "outline",
            "uses_emoji": False,
            "prefers_diagrams": True,
            "learning_preferences": [],
            "custom_style": ""
        }
        
        instruction = _build_system_instruction(style_dna)
        
        print(f"\n  Legacy tone '{tone}': ", end="")
        if f'TONE:' in instruction:
            print("✅ Works")
        else:
            print("❌ Failed")


if __name__ == "__main__":
    print("\n🧪 DNA OPTIONS OUTPUT TEST\n")
    
    try:
        test_cognitive_tones()
        test_learning_preferences()
        test_custom_style()
        test_combined()
        test_legacy_tones()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Review the output above to verify tones are distinct")
        print("2. Check that learning preferences add appropriate guidance")
        print("3. Verify custom style is integrated")
        print("4. Test with actual content generation (upload a file)")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
