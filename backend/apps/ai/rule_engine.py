"""
Tier 3 — Rule-Based Decision Engine
For Consumers and Workers (70-75 agents).
Deterministic rules based on wealth, emotion, and economy conditions.
Fast crowd simulation — no ML overhead.
"""
import logging
import random

logger = logging.getLogger(__name__)

# Action constants
BUY = 'buy'
SELL = 'sell'
SAVE = 'save'
INVEST = 'invest'
PANIC_SELL = 'panic'
COOPERATE = 'cooperate'
WORK = 'work'
QUIT = 'quit'


def decide_consumer(agent, economy: dict) -> tuple:
    """
    Rule-based decision for Consumer agents.
    Returns (action, confidence, reasoning)
    """
    wealth = agent.wealth
    emotion = agent.dominant_emotion
    inflation = economy.get('inflation', 2.0)
    confidence = economy.get('market_confidence', 70.0)
    unemployment = economy.get('unemployment', 5.0)

    # PANIC override
    if emotion == 'panic' or agent.emotion_panic > 0.6:
        return PANIC_SELL, 0.95, 'Panic — selling everything to preserve cash'

    # FEAR: cut spending, save
    if emotion == 'fearful' or agent.emotion_fear > 0.5:
        if wealth < 500:
            return WORK, 0.85, 'Fearful and low wealth — seeking work'
        return SAVE, 0.80, 'Fearful — saving instead of spending'

    # HIGH INFLATION: save to preserve value
    if inflation > 10.0:
        return SAVE, 0.75, f'Inflation {inflation:.1f}% — preserving wealth'

    # WEALTHY + OPTIMISTIC: spend
    if wealth > 2000 and emotion in ('optimistic', 'trusting', 'greedy'):
        return BUY, 0.70, 'Good wealth and positive outlook — spending'

    # LOW WEALTH: work
    if wealth < 300:
        return WORK, 0.90, 'Low wealth — must work to survive'

    # HIGH UNEMPLOYMENT: save cautiously
    if unemployment > 20.0:
        return SAVE, 0.65, f'High unemployment {unemployment:.1f}% — cautious saving'

    # STRESSED: reduce spending
    if emotion == 'stressed':
        return SAVE, 0.60, 'Stressed — reducing expenditure'

    # OPTIMISTIC: buy
    if emotion in ('optimistic', 'trusting'):
        return BUY, 0.65, 'Optimistic — comfortable spending'

    # DEFAULT
    if random.random() < 0.6:
        return SAVE, 0.50, 'Default — cautious saving'
    return BUY, 0.50, 'Default — modest spending'


def decide_worker(agent, economy: dict) -> tuple:
    """
    Rule-based decision for Worker agents.
    Returns (action, confidence, reasoning)
    """
    wealth = agent.wealth
    emotion = agent.dominant_emotion
    unemployment = economy.get('unemployment', 5.0)
    inflation = economy.get('inflation', 2.0)

    # PANIC
    if emotion == 'panic' or agent.emotion_panic > 0.5:
        return PANIC_SELL, 0.90, 'Panic — liquidating assets'

    # QUIT if wealthy enough and fearful
    if wealth > 5000 and emotion == 'fearful':
        return QUIT, 0.60, 'High fear — considering leaving the workforce'

    # WORK if unemployed or low wealth
    if not agent.is_employed or wealth < 500:
        return WORK, 0.95, 'Need employment — seeking work'

    # COOPERATE if trusting
    if emotion in ('trusting', 'cooperative'):
        return COOPERATE, 0.75, 'High trust — cooperating with peers'

    # HIGH INFLATION: demand higher wages (work harder)
    if inflation > 8.0:
        return WORK, 0.70, f'High inflation {inflation:.1f}% — working more to compensate'

    # SAVE if stressed
    if emotion == 'stressed':
        return SAVE, 0.65, 'Stressed worker — saving for security'

    # DEFAULT: work
    return WORK, 0.80, 'Default — continuing work'


RULE_DISPATCH = {
    'consumer': decide_consumer,
    'worker':   decide_worker,
}


def run_rule_decision(agent, economy: dict) -> dict:
    """
    Entry point for Tier 3 rule-based decision.
    Returns a decision dict.
    """
    dispatch = RULE_DISPATCH.get(agent.profession)
    if dispatch is None:
        return {'action': SAVE, 'confidence': 0.5, 'reasoning': 'No rule defined — defaulting to save'}

    action, confidence, reasoning = dispatch(agent, economy)
    return {
        'action': action,
        'confidence': confidence,
        'reasoning': reasoning,
        'tier': 3,
    }