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

from apps.simulation.tuning import (
    EMOTION_DECAY_RATES as EMOTION_DECAY,
    EMOTION_BASELINES as EMOTION_BASELINE,
    TRIGGER_SCALE,
    PANIC_AGENT_FRACTION,
)





# ── Thresholds that define dominant emotion ───────────────────────────────────
DOMINANT_THRESHOLD = 0.35

# ── Economy trigger thresholds ─────────────────────────────────────────────
GDP_GROWTH_OPTIMISM_THRESHOLD = 0.5
GDP_DECLINE_FEAR_THRESHOLD = -0.5
INFLATION_STRESS_THRESHOLD = 6.0
INFLATION_PANIC_THRESHOLD = 15.0
INFLATION_OPTIMISM_THRESHOLD = 2.0   # LOW inflation = optimism, not panic
UNEMPLOYMENT_STRESS_THRESHOLD = 15.0
UNEMPLOYMENT_FEAR_THRESHOLD = 25.0
MARKET_CRASH_THRESHOLD = 40.0
MARKET_BOOM_THRESHOLD = 75.0
SHORTAGE_FEAR_BOOST = 0.004


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
    """
    CORRECTED economic emotion triggers based on real economics:
    - LOW inflation (< 2%) = deflation fear, economic stagnation
    - MODERATE inflation (2-6%) = healthy, mild optimism
    - HIGH inflation (> 10%) = stress, fear
    - VERY HIGH inflation (> 20%) = panic
    - HIGH unemployment = fear, stress
    - GDP growth = optimism
    - GDP decline = fear
    - High market confidence = optimism/greed
    - Low market confidence = fear/panic
    """
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

    # ── Inflation effects ─────────────────────────────────────────────────
    if inflation > INFLATION_PANIC_THRESHOLD:
        # Hyperinflation — fear and stress
        deltas['stress'] += 0.004
        deltas['fear'] += 0.003
        deltas['optimism'] -= 0.002
    elif inflation > INFLATION_STRESS_THRESHOLD:
        # High inflation — stress
        deltas['stress'] += 0.002
        deltas['fear'] += 0.001
    elif 2.0 <= inflation <= INFLATION_STRESS_THRESHOLD:
        # Healthy inflation zone — mild optimism
        deltas['optimism'] += 0.001
        deltas['trust'] += 0.0005
    elif inflation < 0.5:
        # Deflation — fear of economic contraction
        deltas['fear'] += 0.002
        deltas['stress'] += 0.001
        deltas['optimism'] -= 0.001

    # ── Unemployment effects ───────────────────────────────────────────────
    if unemployment > UNEMPLOYMENT_FEAR_THRESHOLD:
        deltas['fear'] += 0.003
        deltas['stress'] += 0.003
        deltas['optimism'] -= 0.002
    elif unemployment > UNEMPLOYMENT_STRESS_THRESHOLD:
        deltas['stress'] += 0.002
        deltas['fear'] += 0.001
    elif unemployment < 3.0:
        # Very low unemployment = some greed/overconfidence
        deltas['greed'] += 0.001
        deltas['optimism'] += 0.001

    # ── GDP growth effects ─────────────────────────────────────────────────
    if gdp_growth > GDP_GROWTH_OPTIMISM_THRESHOLD:
        deltas['optimism'] += min(0.003, gdp_growth * 0.001)
        deltas['greed'] += min(0.002, gdp_growth * 0.0005)
    elif gdp_growth < GDP_DECLINE_FEAR_THRESHOLD:
        deltas['fear'] += min(0.003, abs(gdp_growth) * 0.001)
        deltas['stress'] += min(0.002, abs(gdp_growth) * 0.0005)

    # ── Market confidence effects ─────────────────────────────────────────
    if confidence < MARKET_CRASH_THRESHOLD:
        deltas['panic'] += 0.003
        deltas['fear'] += 0.002
        deltas['trust'] -= 0.001
    elif confidence < 55.0:
        deltas['stress'] += 0.001
        deltas['fear'] += 0.001
    elif confidence > MARKET_BOOM_THRESHOLD:
        deltas['optimism'] += 0.002
        deltas['greed'] += 0.001
        deltas['trust'] += 0.001

    # ── Resource shortages ────────────────────────────────────────────────
    for shortage in shortages:
        deltas['fear'] += SHORTAGE_FEAR_BOOST
        deltas['stress'] += SHORTAGE_FEAR_BOOST * 0.5

    return {k: v * TRIGGER_SCALE for k, v in deltas.items()}

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

def apply_panic_circuit_breaker(agents: list, context: dict) -> list:
    """
    If more than 80% of agents are in panic for too long,
    force a partial reset toward baseline to allow recovery.
    This simulates central bank intervention / market stabilisation.
    """
    panic_count = sum(1 for a in agents if a.dominant_emotion == 'panic')
    panic_ratio = panic_count / len(agents) if agents else 0

    if panic_ratio < 0.80:
        return agents

    policy = context.get('policy_state', {})
    stimulus_active = policy.get('stimulus_active', False)
    gov_spending = policy.get('government_spending', 10000)

    # Only trigger circuit breaker if government is actively intervening
    if not stimulus_active and gov_spending < 100000:
        return agents

    logger.warning(
        f'[Tick {context["tick"]}] PANIC CIRCUIT BREAKER — '
        f'{panic_ratio*100:.0f}% agents in panic. Forcing partial recovery.'
    )

    for agent in agents:
        if agent.dominant_emotion == 'panic':
            # Pull panic down toward recoverable levels
            agent.emotion_panic = max(EMOTION_BASELINE['panic'], agent.emotion_panic * 0.6)
            agent.emotion_fear = max(EMOTION_BASELINE['fear'], agent.emotion_fear * 0.7)
            agent.emotion_optimism = max(0.2, agent.emotion_optimism + 0.08)
            agent.emotion_trust = max(0.3, agent.emotion_trust + 0.05)

    return agents
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
    # Apply panic circuit breaker before processing
    agents = apply_panic_circuit_breaker(agents, context)
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
    