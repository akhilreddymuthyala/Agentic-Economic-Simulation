"""
Social Influence Engine — Phase 5

Propagates dominant emotions through the SocialRelationship graph.
Implements:
- Influence spreading scaled by trust scores
- Herd behavior: resistance drops when majority of connections share emotion
- Panic waves: rapid propagation when cluster fear exceeds threshold
"""
import logging
import random
from collections import defaultdict
from apps.agents.models import Agent, AgentRole
from apps.social.models import SocialRelationship
from apps.emotions.engine import clamp, compute_dominant_emotion

from apps.simulation.tuning import (
    HERD_THRESHOLD,
    PANIC_WAVE_THRESHOLD as PANIC_CLUSTER_THRESHOLD,
    PANIC_WAVE_BOOST,
    SOCIAL_INFLUENCE_SCALE as INFLUENCE_SCALE,
)

logger = logging.getLogger(__name__)


HERD_RESISTANCE_REDUCTION = 0.5
  

# High-influence roles that actively push emotions outward
HIGH_INFLUENCE_ROLES = {
    AgentRole.INFLUENCER,
    AgentRole.GOVERNMENT,
    AgentRole.TRADER,
    AgentRole.BANKER,
}


def build_adjacency(agent_ids: set) -> dict:
    """
    Build adjacency map: agent_id → list of (neighbor_id, trust, influence)
    from SocialRelationship table.
    """
    adj = defaultdict(list)
    rels = SocialRelationship.objects.filter(
        agent_a_id__in=agent_ids,
        agent_b_id__in=agent_ids,
    ).values('agent_a_id', 'agent_b_id', 'trust_score', 'influence_score')

    for rel in rels:
        a = rel['agent_a_id']
        b = rel['agent_b_id']
        t = rel['trust_score']
        inf = rel['influence_score']
        adj[a].append((b, t, inf))
        adj[b].append((a, t, inf))

    return adj


def emotion_to_vector(agent: Agent) -> dict:
    return {
        'fear':     agent.emotion_fear,
        'greed':    agent.emotion_greed,
        'trust':    agent.emotion_trust,
        'optimism': agent.emotion_optimism,
        'stress':   agent.emotion_stress,
        'panic':    agent.emotion_panic,
    }


def dominant_to_vector_boost(dominant: str) -> dict:
    """Convert a dominant emotion string to a boost vector."""
    boost = {k: 0.0 for k in ['fear', 'greed', 'trust', 'optimism', 'stress', 'panic']}
    mapping = {
        'fearful':   'fear',
        'greedy':    'greed',
        'trusting':  'trust',
        'optimistic':'optimism',
        'stressed':  'stress',
        'panic':     'panic',
        'neutral':   None,
    }
    key = mapping.get(dominant)
    if key:
        boost[key] = 1.0
    return boost


def run_social_influence_engine(context: dict) -> dict:
    """
    Main entry point for the social influence engine.
    Runs every tick but only does full graph propagation every 6 ticks
    to keep performance acceptable at scale.
    """
    tick = context['tick']

    # Full propagation every 6 ticks (~every quarter sim day)
    if tick % 6 != 0:
        return context

    agents = list(Agent.objects.filter(is_active=True))
    agent_map = {a.id: a for a in agents}
    agent_ids = set(agent_map.keys())

    adj = build_adjacency(agent_ids)

    # Accumulate emotion deltas for each agent
    deltas = defaultdict(lambda: {
        'fear': 0.0, 'greed': 0.0, 'trust': 0.0,
        'optimism': 0.0, 'stress': 0.0, 'panic': 0.0,
    })

    panic_wave_agents = set()

    for agent_id, neighbors in adj.items():
        if agent_id not in agent_map:
            continue
        agent = agent_map[agent_id]

        if not neighbors:
            continue

        # Count neighbor emotions for herd detection
        neighbor_emotions = []
        for (nb_id, trust, influence) in neighbors:
            if nb_id not in agent_map:
                continue
            nb = agent_map[nb_id]
            neighbor_emotions.append(nb.dominant_emotion)

        total_neighbors = len(neighbor_emotions)
        if total_neighbors == 0:
            continue

        # ── Herd behavior check ───────────────────────────────────────────
        emotion_freq = defaultdict(int)
        for em in neighbor_emotions:
            emotion_freq[em] += 1

        most_common_emotion = max(emotion_freq, key=emotion_freq.get)
        most_common_ratio = emotion_freq[most_common_emotion] / total_neighbors
        herd_active = most_common_ratio >= HERD_THRESHOLD

        # ── Panic wave detection ──────────────────────────────────────────
        panic_ratio = emotion_freq.get('panic', 0) / total_neighbors
        fear_ratio = emotion_freq.get('fearful', 0) / total_neighbors
        if (panic_ratio + fear_ratio) >= PANIC_CLUSTER_THRESHOLD:
            panic_wave_agents.add(agent_id)

        # ── Influence propagation from each neighbor ──────────────────────
        for (nb_id, trust, influence) in neighbors:
            if nb_id not in agent_map:
                continue
            nb = agent_map[nb_id]

            # Only high-influence role agents AND agents with high influence score actively push
            is_high_influence = (
                nb.profession in HIGH_INFLUENCE_ROLES or
                nb.social_influence > 0.7
            )
            if not is_high_influence and random.random() > 0.3:
                continue

            nb_vector = emotion_to_vector(nb)
            agent_vector = emotion_to_vector(agent)

            # Transfer scaled by trust and influence score
            transfer_scale = trust * influence * INFLUENCE_SCALE
            if herd_active:
                transfer_scale *= (1.0 + HERD_RESISTANCE_REDUCTION)

            for emotion_key in ['fear', 'greed', 'trust', 'optimism', 'stress', 'panic']:
                diff = nb_vector[emotion_key] - agent_vector[emotion_key]
                deltas[agent_id][emotion_key] += diff * transfer_scale

    # ── Apply panic wave boosts ───────────────────────────────────────────────
    for agent_id in panic_wave_agents:
        deltas[agent_id]['panic'] += PANIC_WAVE_BOOST
        deltas[agent_id]['fear'] += PANIC_WAVE_BOOST * 0.5

    # ── Apply all deltas and recompute dominant emotions ──────────────────────
    updated = []
    for agent_id, delta in deltas.items():
        if agent_id not in agent_map:
            continue
        agent = agent_map[agent_id]

        agent.emotion_fear = clamp(agent.emotion_fear + delta['fear'])
        agent.emotion_greed = clamp(agent.emotion_greed + delta['greed'])
        agent.emotion_trust = clamp(agent.emotion_trust + delta['trust'])
        agent.emotion_optimism = clamp(agent.emotion_optimism + delta['optimism'])
        agent.emotion_stress = clamp(agent.emotion_stress + delta['stress'])
        agent.emotion_panic = clamp(agent.emotion_panic + delta['panic'])

        agent.dominant_emotion = compute_dominant_emotion(
            agent.emotion_fear, agent.emotion_greed, agent.emotion_trust,
            agent.emotion_optimism, agent.emotion_stress, agent.emotion_panic,
        )
        updated.append(agent)

    if updated:
        Agent.objects.bulk_update(updated, [
            'emotion_fear', 'emotion_greed', 'emotion_trust',
            'emotion_optimism', 'emotion_stress', 'emotion_panic',
            'dominant_emotion',
        ])

    context['panic_wave_agents'] = list(panic_wave_agents)
    context['herd_active'] = len(panic_wave_agents) > 10

    if tick % 24 == 0:
        logger.info(
            f'[Tick {tick}] Social influence propagated. '
            f'Panic wave agents: {len(panic_wave_agents)}'
        )

    return context