"""
Emotion Engine — Phase 5

Per-agent emotion vector: fear, greed, trust, optimism, stress, panic
Each emotion decays toward baseline each tick without reinforcement.
Triggers fire based on economy conditions and resource shortages.
"""
import logging
import random
from django.db.models import Q
from apps.agents.models import Agent, AgentRole, AgentEmotionState

logger = logging.getLogger(__name__)

# ── Decay rates per tick (emotion × decay = reduction per tick) ───────────────
EMOTION_BASELINE = {
    'fear':     0.08,
    'greed':    0.18,
    'trust':    0.45,
    'optimism': 0.35,
    'stress':   0.12,
    'panic':    0.03,
}

# Decay rates — much smaller so emotions don't collapse to zero
EMOTION_DECAY = {
    'fear':     0.008,
    'greed':    0.006,
    'trust':    0.003,
    'optimism': 0.005,
    'stress':   0.010,
    'panic':    0.015,
}


# ── Thresholds that define dominant emotion ───────────────────────────────────
DOMINANT_THRESHOLD = 0.35

# ── Economy trigger thresholds ────────────────────────────────────────────────
GDP_GROWTH_OPTIMISM_THRESHOLD = 0.5      # % growth triggers optimism
GDP_DECLINE_FEAR_THRESHOLD = -0.5        # % decline triggers fear
INFLATION_STRESS_THRESHOLD = 8.0        # inflation above this → stress
INFLATION_PANIC_THRESHOLD = 20.0        # inflation above this → panic
UNEMPLOYMENT_STRESS_THRESHOLD = 15.0   # unemployment above this → stress
MARKET_CRASH_THRESHOLD = 40.0          # confidence below this → panic
MARKET_BOOM_THRESHOLD = 80.0           # confidence above this → optimism
SHORTAGE_FEAR_BOOST = 0.08             # fear boost per shortage event


def compute_dominant_emotion(fear, greed, trust, optimism, stress, panic) -> str:
    # Panic overrides everything at low threshold
    if panic >= 0.35:
        return AgentEmotionState.PANIC
    # Fear overrides at moderate threshold
    if fear >= 0.45:
        return AgentEmotionState.FEARFUL
    # Stress overrides if high
    if stress >= 0.45:
        return AgentEmotionState.STRESSED

    emotions = {
        'fear':     fear,
        'greed':    greed,
        'trust':    trust,
        'optimism': optimism,
        'stress':   stress,
        'panic':    panic,
    }

    max_val = max(emotions.values())
    second_max = sorted(emotions.values())[-2]

    # Only assign dominant if it clearly leads by 0.1 margin
    if max_val - second_max < 0.10:
        return AgentEmotionState.NEUTRAL

    dominant = max(emotions, key=emotions.get)
    mapping = {
        'fear':     AgentEmotionState.FEARFUL,
        'greed':    AgentEmotionState.GREEDY,
        'trust':    AgentEmotionState.TRUSTING,
        'optimism': AgentEmotionState.OPTIMISTIC,
        'stress':   AgentEmotionState.STRESSED,
        'panic':    AgentEmotionState.PANIC,
    }
    return mapping.get(dominant, AgentEmotionState.NEUTRAL)


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def compute_economy_triggers(context: dict) -> dict:
    eco = context['economy']
    shortages = context.get('resource_shortages', [])
    gdp_growth = eco.get('gdp_growth_rate', 0.0)
    inflation = eco.get('inflation', 2.0)
    unemployment = eco.get('unemployment', 5.0)
    confidence = eco.get('market_confidence', 70.0)

    deltas = {
        'fear': 0.0, 'greed': 0.0, 'trust': 0.0,
        'optimism': 0.0, 'stress': 0.0, 'panic': 0.0,
    }

    # GDP growth → optimism / fear
    if gdp_growth > GDP_GROWTH_OPTIMISM_THRESHOLD:
        deltas['optimism'] += min(0.005, gdp_growth * 0.002)
        deltas['greed'] += min(0.003, gdp_growth * 0.001)
    elif gdp_growth < GDP_DECLINE_FEAR_THRESHOLD:
        deltas['fear'] += min(0.005, abs(gdp_growth) * 0.002)
        deltas['stress'] += min(0.003, abs(gdp_growth) * 0.001)

    # Inflation stress / panic — only trigger at very high levels
    if inflation > INFLATION_PANIC_THRESHOLD:
        deltas['panic'] += 0.003
        deltas['fear'] += 0.003
        deltas['stress'] += 0.002
    elif inflation > INFLATION_STRESS_THRESHOLD:
        deltas['stress'] += 0.002
        deltas['fear'] += 0.001

    # Unemployment stress
    if unemployment > UNEMPLOYMENT_STRESS_THRESHOLD:
        deltas['stress'] += 0.002
        deltas['fear'] += 0.001
        deltas['optimism'] -= 0.001

    # Market confidence
    if confidence < MARKET_CRASH_THRESHOLD:
        deltas['panic'] += 0.002
        deltas['fear'] += 0.002
        deltas['trust'] -= 0.001
    elif confidence > MARKET_BOOM_THRESHOLD:
        deltas['optimism'] += 0.002
        deltas['greed'] += 0.001
        deltas['trust'] += 0.001

    # Resource shortages
    for shortage in shortages:
        deltas['fear'] += 0.003
        deltas['stress'] += 0.001

    return deltas


def apply_decay(agent: Agent) -> Agent:
    """Decay toward baseline — never below baseline floor."""
    for field, key in [
        ('emotion_fear', 'fear'), ('emotion_greed', 'greed'),
        ('emotion_trust', 'trust'), ('emotion_optimism', 'optimism'),
        ('emotion_stress', 'stress'), ('emotion_panic', 'panic'),
    ]:
        current = getattr(agent, field)
        baseline = EMOTION_BASELINE[key]
        decay = EMOTION_DECAY[key]
        # Pull toward baseline from either direction
        new_val = current + (baseline - current) * decay
        # Never go below baseline floor
        new_val = max(baseline * 0.5, new_val)
        setattr(agent, field, clamp(new_val))
    return agent


def apply_triggers(agent: Agent, deltas: dict,
                   role_sensitivity: float = 1.0) -> Agent:
    """Apply economy trigger deltas to an agent, scaled by role sensitivity."""
    agent.emotion_fear = clamp(agent.emotion_fear + deltas['fear'] * role_sensitivity)
    agent.emotion_greed = clamp(agent.emotion_greed + deltas['greed'] * role_sensitivity)
    agent.emotion_trust = clamp(agent.emotion_trust + deltas['trust'] * role_sensitivity)
    agent.emotion_optimism = clamp(agent.emotion_optimism + deltas['optimism'] * role_sensitivity)
    agent.emotion_stress = clamp(agent.emotion_stress + deltas['stress'] * role_sensitivity)
    agent.emotion_panic = clamp(agent.emotion_panic + deltas['panic'] * role_sensitivity)
    return agent


# Role sensitivity — how strongly each role reacts to economy triggers
ROLE_SENSITIVITY = {
    AgentRole.CONSUMER:          1.2,
    AgentRole.WORKER:            1.1,
    AgentRole.TRADER:            0.9,
    AgentRole.INVESTOR:          0.8,
    AgentRole.BUSINESS_OWNER:    0.85,
    AgentRole.MANUFACTURER:      0.8,
    AgentRole.GOVERNMENT:        0.4,
    AgentRole.BANKER:            0.6,
    AgentRole.INFLUENCER:        0.7,
    AgentRole.RESEARCHER:        0.6,
    AgentRole.RESOURCE_SUPPLIER: 0.9,
}


def run_emotion_engine(context: dict) -> dict:
    """
    Main emotion engine entry point.
    1. Compute economy-based trigger deltas
    2. For each active agent: decay → apply triggers → resolve dominant emotion
    3. Bulk update all agents
    4. Write emotion logs every 24 ticks
    """
    tick = context['tick']
    trigger_deltas = compute_economy_triggers(context)

    agents = list(Agent.objects.filter(is_active=True))
    updated = []

    emotion_counts = {e: 0 for e in AgentEmotionState.values}

    for agent in agents:
        # 1. Decay
        agent = apply_decay(agent)

        # 2. Apply economy triggers scaled by role sensitivity
        sensitivity = ROLE_SENSITIVITY.get(agent.profession, 1.0)
        agent = apply_triggers(agent, trigger_deltas, sensitivity)

        # 3. Resolve dominant emotion
        agent.dominant_emotion = compute_dominant_emotion(
            agent.emotion_fear, agent.emotion_greed, agent.emotion_trust,
            agent.emotion_optimism, agent.emotion_stress, agent.emotion_panic,
        )

        emotion_counts[agent.dominant_emotion] = emotion_counts.get(agent.dominant_emotion, 0) + 1
        updated.append(agent)

    Agent.objects.bulk_update(updated, [
        'emotion_fear', 'emotion_greed', 'emotion_trust',
        'emotion_optimism', 'emotion_stress', 'emotion_panic',
        'dominant_emotion',
    ])

    # Write emotion logs every 24 ticks
    if tick % 24 == 0:
        _write_emotion_logs(updated, tick, context)
        logger.info(
            f'[Tick {tick}] Emotions — '
            + ' '.join(f'{k}:{v}' for k, v in emotion_counts.items() if v > 0)
        )

    context['emotion_distribution'] = emotion_counts
    context['trigger_deltas'] = trigger_deltas
    return context


def _write_emotion_logs(agents: list, tick: int, context: dict):
    from apps.emotions.models import AgentEmotionLog
    logs = [
        AgentEmotionLog(
            agent_id=a.id,
            fear=a.emotion_fear,
            greed=a.emotion_greed,
            trust=a.emotion_trust,
            optimism=a.emotion_optimism,
            stress=a.emotion_stress,
            panic=a.emotion_panic,
            dominant_emotion=a.dominant_emotion,
            tick_number=tick,
        )
        for a in agents
    ]
    AgentEmotionLog.objects.bulk_create(logs)
    