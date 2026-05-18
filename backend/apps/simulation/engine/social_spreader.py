"""
Step 4: Spread Social Effects — now calls real emotion and social engines.
"""
import logging
from apps.emotions.engine import run_emotion_engine
from apps.social.engine import run_social_influence_engine
from apps.emotions.behavior_mapper import apply_behavioral_effects

logger = logging.getLogger(__name__)


def spread_social_effects(context: dict) -> dict:
    """
    Execute in order:
    1. Emotion engine — decay + economy triggers
    2. Social influence engine — graph propagation
    3. Behavioral effect mapper — emotion → economy modifiers
    """
    context = run_emotion_engine(context)
    context = run_social_influence_engine(context)
    context = apply_behavioral_effects(context)
    return context