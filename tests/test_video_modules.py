"""
Unit tests for video generation modules (Style Sequencer and Triad Formula)
"""

import pytest
from agents.synthesis.video_sequencer import (
    sequence_video_acts,
    build_veo_prompt,
    build_transition_prompt,
    STYLE_PRIORITY_ORDER,
    VEO_MODES
)
from agents.synthesis.prompt_optimizer import (
    categorize_topic,
    select_veo_strength,
    build_optimized_prompt,
    TopicCategory,
    VeoStrength
)


class TestStyleSequencer:
    """Tests for Style Sequencer module"""
    
    def test_sequence_all_styles(self):
        """Test sequencing with all 4 styles selected"""
        user_prefs = ['real_world', 'analogies', 'concept_map', 'practice_set']
        result = sequence_video_acts(user_prefs, total_duration=300)
        
        assert len(result) == 4
        assert result[0]['style'] == 'real_world'
        assert result[1]['style'] == 'analogies'
        assert result[2]['style'] == 'concept_map'
        assert result[3]['style'] == 'practice_set'
        
        # Each act should get ~75 seconds (300 / 4)
        for act in result:
            assert act['total_duration'] == 75
            assert act['segments'] == 9  # 75 / 8
            assert act['segment_duration'] == 8
    
    def test_sequence_partial_styles(self):
        """Test sequencing with only 2 styles selected"""
        user_prefs = ['analogies', 'real_world']  # Out of order
        result = sequence_video_acts(user_prefs, total_duration=300)
        
        # Should reorder to pedagogical sequence
        assert len(result) == 2
        assert result[0]['style'] == 'real_world'  # Comes first
        assert result[1]['style'] == 'analogies'   # Comes second
        
        # Each act should get 150 seconds
        for act in result:
            assert act['total_duration'] == 150
            assert act['segments'] == 18  # 150 / 8
    
    def test_sequence_empty_preferences(self):
        """Test fallback when no preferences provided"""
        result = sequence_video_acts([], total_duration=300)
        
        # Should default to real_world + concept_map
        assert len(result) == 2
        assert result[0]['style'] == 'real_world'
        assert result[1]['style'] == 'concept_map'
    
    def test_sequence_custom_duration(self):
        """Test with custom duration (e.g., 120 seconds)"""
        user_prefs = ['real_world', 'analogies']
        result = sequence_video_acts(user_prefs, total_duration=120)
        
        assert len(result) == 2
        for act in result:
            assert act['total_duration'] == 60
            assert act['segments'] == 7  # 60 / 8
    
    def test_veo_modes_present(self):
        """Test that all acts have proper Veo modes"""
        user_prefs = ['real_world', 'concept_map']
        result = sequence_video_acts(user_prefs)
        
        for act in result:
            assert 'veo_mode' in act
            assert 'visual_style' in act['veo_mode']
            assert 'camera' in act['veo_mode']
            assert 'lighting' in act['veo_mode']
            assert 'audio' in act['veo_mode']
    
    def test_build_veo_prompt_basic(self):
        """Test basic Veo prompt generation"""
        act = {
            'style': 'real_world',
            'veo_mode': VEO_MODES['real_world']
        }
        
        prompt = build_veo_prompt(
            act=act,
            topic="Photosynthesis",
            narrative="Sunlight hits a green leaf in a rainforest",
            segment_index=0
        )
        
        assert "Cinematic documentary footage" in prompt
        assert "Photosynthesis" in prompt
        assert "Sunlight hits a green leaf" in prompt
        assert "Natural ambient sounds" in prompt
    
    def test_build_veo_prompt_with_continuation(self):
        """Test prompt with continuation hint"""
        act = {
            'style': 'analogies',
            'veo_mode': VEO_MODES['analogies']
        }
        
        prompt = build_veo_prompt(
            act=act,
            topic="Electricity",
            narrative="Water flows through pipes",
            segment_index=3  # Not first segment
        )
        
        assert "Continue from previous segment" in prompt
        assert "Surrealist visual metaphor" in prompt
    
    def test_build_transition_prompt(self):
        """Test transition prompt generation"""
        from_act = {'style': 'real_world'}
        to_act = {'style': 'analogies'}
        
        transition = build_transition_prompt(from_act, to_act, "Photosynthesis")
        
        assert "morphs" in transition.lower() or "transform" in transition.lower()
        assert len(transition) > 20  # Should be descriptive


class TestTriadFormula:
    """Tests for Triad Formula (Prompt Optimizer) module"""
    
    def test_categorize_hard_science(self):
        """Test categorization of hard science topics"""
        category = categorize_topic(
            topic="Quantum Mechanics",
            content="Physics quantum particles wave function"
        )
        assert category == TopicCategory.HARD_SCIENCE
        
        category = categorize_topic(
            topic="Photosynthesis",
            content="Biology cellular molecular chemistry"
        )
        assert category == TopicCategory.HARD_SCIENCE
    
    def test_categorize_humanities(self):
        """Test categorization of humanities topics"""
        category = categorize_topic(
            topic="French Revolution",
            content="History society culture revolution 18th century"
        )
        assert category == TopicCategory.HUMANITIES
        
        category = categorize_topic(
            topic="Shakespeare",
            content="Literature poetry novel art renaissance"
        )
        assert category == TopicCategory.HUMANITIES
    
    def test_categorize_soft_skills(self):
        """Test categorization of soft skills topics"""
        category = categorize_topic(
            topic="Leadership",
            content="Business management teamwork communication strategy"
        )
        assert category == TopicCategory.SOFT_SKILLS
        
        category = categorize_topic(
            topic="Negotiation",
            content="Psychology persuasion influence decision making"
        )
        assert category == TopicCategory.SOFT_SKILLS
    
    def test_categorize_ambiguous(self):
        """Test categorization with minimal keywords"""
        category = categorize_topic(
            topic="General Topic",
            content="Some random content"
        )
        # Should default to HARD_SCIENCE
        assert category == TopicCategory.HARD_SCIENCE
    
    def test_select_veo_strength_hard_science(self):
        """Test Veo strength selection for hard science"""
        strength = select_veo_strength(
            TopicCategory.HARD_SCIENCE, 
            'real_world'
        )
        assert strength == VeoStrength.PHYSICS_SIM
        
        strength = select_veo_strength(
            TopicCategory.HARD_SCIENCE, 
            'analogies'
        )
        assert strength == VeoStrength.VISUAL_METAPHOR
    
    def test_select_veo_strength_humanities(self):
        """Test Veo strength selection for humanities"""
        strength = select_veo_strength(
            TopicCategory.HUMANITIES, 
            'real_world'
        )
        assert strength == VeoStrength.ATMOSPHERIC_IMMERSION
        
        strength = select_veo_strength(
            TopicCategory.HUMANITIES, 
            'concept_map'
        )
        assert strength == VeoStrength.TEMPORAL_FLOW
    
    def test_select_veo_strength_soft_skills(self):
        """Test Veo strength selection for soft skills"""
        strength = select_veo_strength(
            TopicCategory.SOFT_SKILLS, 
            'practice_set'
        )
        assert strength == VeoStrength.HUMAN_NUANCE
    
    def test_build_optimized_prompt_complete(self):
        """Test complete optimized prompt generation"""
        prompt = build_optimized_prompt(
            topic="Doppler Effect",
            narrative="A glowing sound wave as a soft blue sphere",
            user_style="analogies",
            cognitive_tone="beginner_friendly",
            topic_category=TopicCategory.HARD_SCIENCE,
            base_veo_mode=VEO_MODES['analogies']
        )
        
        # Check all components are present
        assert "[Cinematic Style]" in prompt
        assert "[Subject Action]" in prompt
        assert "[Environment/Lighting]" in prompt
        assert "[Veo 3 Technical Trigger]" in prompt
        assert "[Audio Cue]" in prompt
        assert "Pacing:" in prompt
        
        # Check specific content
        assert "Slow smooth panning" in prompt  # beginner_friendly camera
        assert "Soft pastel palette" in prompt  # beginner_friendly lighting
        assert "Gentle, unhurried" in prompt    # beginner_friendly pacing
        assert "Surrealist dream logic" in prompt  # Visual metaphor trigger (analogies style)
    
    def test_build_optimized_prompt_coaching_tone(self):
        """Test prompt with coaching tone"""
        prompt = build_optimized_prompt(
            topic="French Revolution",
            narrative="Chaotic crowd in Paris streets",
            user_style="real_world",
            cognitive_tone="coaching",
            topic_category=TopicCategory.HUMANITIES,
            base_veo_mode=VEO_MODES['real_world']
        )
        
        assert "Dynamic push-in" in prompt
        assert "Warm golden hour" in prompt
        assert "Energetic" in prompt
        assert "Period-accurate" in prompt  # Atmospheric immersion


class TestIntegration:
    """Integration tests combining both modules"""
    
    def test_full_workflow_photosynthesis(self):
        """Test complete workflow for Photosynthesis topic"""
        # Step 1: User preferences
        user_prefs = ['real_world', 'analogies', 'concept_map']
        
        # Step 2: Sequence acts
        acts = sequence_video_acts(user_prefs, total_duration=240)
        assert len(acts) == 3
        
        # Step 3: Categorize topic
        topic_category = categorize_topic(
            "Photosynthesis",
            "Biology cellular process plants sunlight energy"
        )
        assert topic_category == TopicCategory.HARD_SCIENCE
        
        # Step 4: Generate optimized prompts for each act
        for act in acts:
            prompt = build_optimized_prompt(
                topic="Photosynthesis",
                narrative=f"Act {act['act']} narrative",
                user_style=act['style'],
                cognitive_tone="textbook",
                topic_category=topic_category,
                base_veo_mode=act['veo_mode']
            )
            
            assert len(prompt) > 100  # Should be substantial
            assert "[Cinematic Style]" in prompt
            assert "Photosynthesis" in prompt or "Act" in prompt
    
    def test_full_workflow_french_revolution(self):
        """Test complete workflow for French Revolution topic"""
        user_prefs = ['real_world', 'concept_map']
        
        acts = sequence_video_acts(user_prefs, total_duration=120)
        
        topic_category = categorize_topic(
            "French Revolution",
            "History 18th century France society political revolution"
        )
        assert topic_category == TopicCategory.HUMANITIES
        
        # First act should use atmospheric immersion
        strength = select_veo_strength(topic_category, acts[0]['style'])
        assert strength == VeoStrength.ATMOSPHERIC_IMMERSION
        
        # Second act should use temporal flow
        strength = select_veo_strength(topic_category, acts[1]['style'])
        assert strength == VeoStrength.TEMPORAL_FLOW


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
