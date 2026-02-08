# Style Sequencer Module for Video Generation

## Overview

The Style Sequencer creates a coherent narrative arc for educational videos by ordering user's learning style preferences in pedagogical sequence. This ensures videos follow the "Hero's Journey" of learning.

## The Algorithm

```python
# agents/synthesis/video_sequencer.py

from typing import List, Dict

# The Pedagogical Order (Narrative Arc)
STYLE_PRIORITY_ORDER = [
    'real_world',   # ACT 1: Hook & Context (Why do I care?)
    'analogies',    # ACT 2: Conceptual Bridge (What is it like?)
    'concept_map',  # ACT 3: Structural Deep Dive (How does it work?)
    'practice_set'  # ACT 4: Application (Can I use it?)
]

# Veo 3 Visual Modes for Each Style
VEO_MODES = {
    'real_world': {
        'visual_style': 'Cinematic documentary footage',
        'camera': 'Handheld camera movement',
        'lighting': 'Natural lighting',
        'quality': 'High fidelity textures',
        'setting': 'Real humans in real environments'
    },
    'analogies': {
        'visual_style': 'Surrealist visual metaphor',
        'camera': 'Smooth, dream-like transitions',
        'lighting': 'Soft, magical lighting',
        'quality': 'Clean composition',
        'setting': 'Metaphorical objects behaving like the concept'
    },
    'concept_map': {
        'visual_style': '3D Motion Graphics',
        'camera': 'Smooth fly-through camera motion',
        'lighting': 'Glowing elements in dark void',
        'quality': 'Data visualization style',
        'setting': 'Nodes and connecting lines, Minority Report UI aesthetic'
    },
    'practice_set': {
        'visual_style': 'First-Person POV simulation',
        'camera': 'Immersive POV, camera interacts with objects',
        'lighting': 'Realistic scenario lighting',
        'quality': 'Interactive simulation',
        'setting': 'Pauses at critical decision points'
    }
}


def sequence_video_acts(user_preferences: List[str], total_duration: int = 300) -> List[Dict]:
    """
    Generate video skeleton based on user's active learning styles.
    
    Args:
        user_preferences: List of user's selected learning styles
        total_duration: Total video duration in seconds (default 300 = 5 min)
    
    Returns:
        List of acts with style, duration, and Veo mode
    """
    # Filter for user selections in pedagogical order
    active_styles = [
        style for style in STYLE_PRIORITY_ORDER 
        if style in user_preferences
    ]
    
    # Fallback: If user selected nothing, default to real_world + concept_map
    if not active_styles:
        active_styles = ['real_world', 'concept_map']
    
    # Calculate duration per act (each act gets multiple 8s segments)
    duration_per_act = total_duration // len(active_styles)
    segments_per_act = duration_per_act // 8  # 8 seconds per Veo segment
    
    # Generate the skeleton
    video_skeleton = []
    for index, style in enumerate(active_styles):
        video_skeleton.append({
            'act': index + 1,
            'style': style,
            'total_duration': duration_per_act,
            'segments': segments_per_act,
            'segment_duration': 8,
            'veo_mode': VEO_MODES[style]
        })
    
    return video_skeleton


def build_veo_prompt(
    act: Dict,
    topic: str,
    narrative: str,
    segment_index: int = 0
) -> str:
    """
    Build Veo 3 prompt for a specific act and segment.
    
    Args:
        act: Act dictionary from sequence_video_acts
        topic: The educational topic
        narrative: The narrative for this act
        segment_index: Which segment within the act (for continuity)
    
    Returns:
        Veo 3 prompt string
    """
    mode = act['veo_mode']
    style = act['style']
    
    # Base prompt structure
    prompt_parts = [
        f"{mode['visual_style']}.",
        f"{mode['camera']}.",
        f"{mode['lighting']}.",
        f"{mode['quality']}.",
        f"{mode['setting']}.",
        f"\n\nTopic: {topic}",
        f"Narrative: {narrative}",
    ]
    
    # Add transition hint for non-first segments
    if segment_index > 0:
        prompt_parts.append(
            f"Continue from previous segment with smooth transition."
        )
    
    # Add audio cues based on style
    if style == 'real_world':
        prompt_parts.append(
            'Audio: Natural ambient sounds, professional narrator voiceover.'
        )
    elif style == 'analogies':
        prompt_parts.append(
            'Audio: Whimsical sound effects, friendly explanatory voiceover.'
        )
    elif style == 'concept_map':
        prompt_parts.append(
            'Audio: Subtle electronic hum, clear technical narration.'
        )
    elif style == 'practice_set':
        prompt_parts.append(
            'Audio: Interactive scenario sounds, pause for user thinking.'
        )
    
    return ' '.join(prompt_parts)


def build_transition_prompt(from_act: Dict, to_act: Dict, topic: str) -> str:
    """
    Build "morph cut" transition prompt between acts.
    
    Args:
        from_act: Previous act dictionary
        to_act: Next act dictionary
        topic: The educational topic
    
    Returns:
        Veo 3 transition prompt
    """
    from_style = from_act['style']
    to_style = to_act['style']
    
    transition_templates = {
        ('real_world', 'analogies'): 
            f"The real-world {topic} object morphs and transforms into a metaphorical representation. "
            f"Smooth dissolve transition from documentary realism to whimsical animation.",
        
        ('analogies', 'concept_map'):
            f"The metaphorical objects dissolve into glowing data points. "
            f"Zoom out to reveal the full system diagram. Transition from soft lighting to dark void with glowing elements.",
        
        ('concept_map', 'practice_set'):
            f"The abstract diagram zooms into one specific node, which expands into a realistic scenario. "
            f"Transition from 3D graphics to first-person POV simulation.",
        
        ('real_world', 'concept_map'):
            f"The real-world scene freezes and fragments into data visualization. "
            f"Camera pulls back to reveal the underlying system structure.",
        
        ('real_world', 'practice_set'):
            f"The documentary footage transitions to first-person perspective. "
            f"The viewer becomes an active participant in the scenario.",
        
        ('analogies', 'practice_set'):
            f"The metaphorical scene solidifies into a realistic interactive scenario. "
            f"Transition from whimsical to practical application."
    }
    
    key = (from_style, to_style)
    template = transition_templates.get(key, 
        f"Smooth transition from {from_style} visual style to {to_style} visual style.")
    
    return template
```

## Integration with Synthesis Agent

The synthesis agent will use this module to:

1. **Analyze user's DNA** to get active learning styles
2. **Call `sequence_video_acts()`** to get the narrative structure
3. **For each act**:
   - Generate narrative content using LLM
   - Split into 8-second segments
   - Build Veo prompts using `build_veo_prompt()`
   - Generate transition prompts between acts
4. **Queue all segments** for async generation
5. **Stitch segments** together when all complete

## Example Output

For a user with all 4 styles selected, studying "Photosynthesis":

```python
skeleton = sequence_video_acts(['real_world', 'analogies', 'concept_map', 'practice_set'])

# Result:
[
    {
        'act': 1,
        'style': 'real_world',
        'total_duration': 75,  # 75 seconds
        'segments': 9,          # 9 x 8s segments
        'segment_duration': 8,
        'veo_mode': {...}
    },
    {
        'act': 2,
        'style': 'analogies',
        'total_duration': 75,
        'segments': 9,
        'segment_duration': 8,
        'veo_mode': {...}
    },
    # ... acts 3 and 4
]
```

## Benefits

1. **Coherent Narrative**: Follows pedagogical best practices
2. **Visual Variety**: Each act has distinct cinematic style
3. **Prevents Drift**: Fresh Veo generation per segment
4. **Flexible**: Works with any combination of user preferences
5. **Scalable**: Easy to adjust total duration or segment length
