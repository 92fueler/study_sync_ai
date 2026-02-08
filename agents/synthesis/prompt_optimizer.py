"""
Prompt Optimizer Module (Triad Formula)

Topic-aware prompt optimization that selects best Veo 3 capabilities
based on topic type, user style, and cognitive tone.
"""

from typing import Dict, Tuple
from enum import Enum


class TopicCategory(Enum):
    """Categories of educational topics"""
    HARD_SCIENCE = "hard_science"  # Physics, Chemistry, Engineering
    HUMANITIES = "humanities"      # History, Literature, Art
    SOFT_SKILLS = "soft_skills"    # Business, Psychology, Communication


class VeoStrength(Enum):
    """Veo 3 technical strengths"""
    PHYSICS_SIM = "physics_simulation"
    VISUAL_METAPHOR = "visual_metaphor"
    ATMOSPHERIC_IMMERSION = "atmospheric_immersion"
    TEMPORAL_FLOW = "temporal_flow"
    HUMAN_NUANCE = "human_nuance"


# Strength Selector Matrix
STRENGTH_MATRIX = {
    (TopicCategory.HARD_SCIENCE, 'real_world'): VeoStrength.PHYSICS_SIM,
    (TopicCategory.HARD_SCIENCE, 'textbook'): VeoStrength.PHYSICS_SIM,
    (TopicCategory.HARD_SCIENCE, 'analogies'): VeoStrength.VISUAL_METAPHOR,
    (TopicCategory.HARD_SCIENCE, 'concept_map'): VeoStrength.VISUAL_METAPHOR,
    
    (TopicCategory.HUMANITIES, 'real_world'): VeoStrength.ATMOSPHERIC_IMMERSION,
    (TopicCategory.HUMANITIES, 'coaching'): VeoStrength.ATMOSPHERIC_IMMERSION,
    (TopicCategory.HUMANITIES, 'concept_map'): VeoStrength.TEMPORAL_FLOW,
    
    (TopicCategory.SOFT_SKILLS, 'practice_set'): VeoStrength.HUMAN_NUANCE,
    (TopicCategory.SOFT_SKILLS, 'real_world'): VeoStrength.HUMAN_NUANCE,
}

# Veo 3 Technical Triggers for Each Strength
VEO_TRIGGERS = {
    VeoStrength.PHYSICS_SIM: {
        'technical': 'Realistic soft-body physics, accurate gravity and collision',
        'examples': ['fluid dynamics', 'zero-gravity', 'squash and stretch', 'particle systems']
    },
    VeoStrength.VISUAL_METAPHOR: {
        'technical': 'Surrealist dream logic, morphing between concepts',
        'examples': ['electricity as water', 'data as flowing rivers', 'abstract to concrete']
    },
    VeoStrength.ATMOSPHERIC_IMMERSION: {
        'technical': 'Period-accurate details, high-fidelity audio, environmental storytelling',
        'examples': ['crowd ambience', 'echoing acoustics', 'weather effects', 'era-specific sounds']
    },
    VeoStrength.TEMPORAL_FLOW: {
        'technical': 'High temporal consistency, smooth time-lapse transitions',
        'examples': ['city growth over centuries', 'plant lifecycle', 'geological changes']
    },
    VeoStrength.HUMAN_NUANCE: {
        'technical': 'Subtle micro-expressions, natural body language, avoiding uncanny valley',
        'examples': ['nervous ticking', 'eye contact', 'genuine smiles', 'hesitation']
    }
}

# Cognitive Tone Modifiers (The "Goldilocks" Tuning)
TONE_MODIFIERS = {
    'textbook': {
        'camera': 'Stable tripod shot',
        'lighting': 'Even lighting, neutral colors',
        'focus': 'Sharp focus throughout',
        'pacing': 'Steady, methodical'
    },
    'coaching': {
        'camera': 'Dynamic push-in camera movement',
        'lighting': 'Warm golden hour lighting',
        'focus': 'Selective focus on subject',
        'pacing': 'Energetic, quick cuts'
    },
    'beginner_friendly': {
        'camera': 'Slow smooth panning',
        'lighting': 'Soft pastel palette',
        'focus': 'Minimalist composition',
        'pacing': 'Gentle, unhurried'
    },
    'key_points': {
        'camera': 'Quick snap zooms to details',
        'lighting': 'High contrast, bold colors',
        'focus': 'Rapid focus shifts',
        'pacing': 'Fast-paced, punchy'
    }
}


def categorize_topic(topic: str, content: str) -> TopicCategory:
    """
    Analyze topic and content to determine category.
    
    Args:
        topic: The topic title
        content: The content text
    
    Returns:
        TopicCategory enum
    """
    # Keywords for classification
    hard_science_keywords = [
        'physics', 'chemistry', 'engineering', 'mathematics', 
        'biology', 'mechanics', 'thermodynamics', 'quantum',
        'calculus', 'algebra', 'geometry', 'statistics',
        'molecular', 'atomic', 'cellular', 'genetic'
    ]
    
    humanities_keywords = [
        'history', 'literature', 'art', 'philosophy', 
        'culture', 'society', 'revolution', 'renaissance',
        'poetry', 'novel', 'painting', 'sculpture',
        'ancient', 'medieval', 'modern', 'contemporary'
    ]
    
    soft_skills_keywords = [
        'business', 'psychology', 'communication', 'leadership',
        'negotiation', 'emotional', 'social', 'management',
        'teamwork', 'collaboration', 'persuasion', 'influence',
        'decision', 'strategy', 'planning', 'organization'
    ]
    
    topic_lower = topic.lower()
    content_lower = content.lower()
    combined = f"{topic_lower} {content_lower}"
    
    # Count keyword matches
    hard_science_count = sum(1 for kw in hard_science_keywords if kw in combined)
    humanities_count = sum(1 for kw in humanities_keywords if kw in combined)
    soft_skills_count = sum(1 for kw in soft_skills_keywords if kw in combined)
    
    # Return category with most matches
    max_count = max(hard_science_count, humanities_count, soft_skills_count)
    
    if max_count == 0:
        # Default to hard science if no matches
        return TopicCategory.HARD_SCIENCE
    
    if hard_science_count == max_count:
        return TopicCategory.HARD_SCIENCE
    elif humanities_count == max_count:
        return TopicCategory.HUMANITIES
    else:
        return TopicCategory.SOFT_SKILLS


def select_veo_strength(
    topic_category: TopicCategory, 
    user_style: str
) -> VeoStrength:
    """
    Select the best Veo 3 strength based on topic and style.
    
    Args:
        topic_category: The topic category
        user_style: User's learning style preference
    
    Returns:
        VeoStrength enum
    """
    key = (topic_category, user_style)
    
    # Direct match
    if key in STRENGTH_MATRIX:
        return STRENGTH_MATRIX[key]
    
    # Fallback logic based on topic category
    if topic_category == TopicCategory.HARD_SCIENCE:
        return (VeoStrength.PHYSICS_SIM 
                if user_style in ['real_world', 'textbook'] 
                else VeoStrength.VISUAL_METAPHOR)
    elif topic_category == TopicCategory.HUMANITIES:
        return VeoStrength.ATMOSPHERIC_IMMERSION
    else:
        return VeoStrength.HUMAN_NUANCE


def build_optimized_prompt(
    topic: str,
    narrative: str,
    user_style: str,
    cognitive_tone: str,
    topic_category: TopicCategory,
    base_veo_mode: Dict
) -> str:
    """
    Build optimized Veo 3 prompt using Triad Formula.
    
    Template: [Cinematic Style] + [Subject Action] + [Environment] + [Veo Trigger] + [Audio Cue]
    
    Args:
        topic: The educational topic
        narrative: The narrative content
        user_style: User's learning style
        cognitive_tone: User's cognitive tone preference
        topic_category: Categorized topic type
        base_veo_mode: Base Veo mode from Style Sequencer
    
    Returns:
        Optimized Veo 3 prompt string
    """
    # Select Veo strength
    strength = select_veo_strength(topic_category, user_style)
    trigger = VEO_TRIGGERS[strength]
    
    # Get tone modifiers
    tone_mod = TONE_MODIFIERS.get(cognitive_tone, TONE_MODIFIERS['textbook'])
    
    # Build prompt components
    cinematic_style = f"{tone_mod['camera']}. {base_veo_mode['camera']}."
    
    subject_action = f"{narrative}"
    
    environment = f"{base_veo_mode['lighting']}. {tone_mod['lighting']}. {tone_mod['focus']}."
    
    veo_trigger = f"{trigger['technical']}."
    
    # Audio cue from base mode
    audio_cue = base_veo_mode.get('audio', 'Natural ambient audio.')
    
    # Assemble final prompt
    prompt_parts = [
        f"[Cinematic Style] {cinematic_style}",
        f"[Subject Action] {subject_action}",
        f"[Environment/Lighting] {environment}",
        f"[Veo 3 Technical Trigger] {veo_trigger}",
        f"[Audio Cue] {audio_cue}",
        f"\n\nPacing: {tone_mod['pacing']}"
    ]
    
    return ' '.join(prompt_parts)
