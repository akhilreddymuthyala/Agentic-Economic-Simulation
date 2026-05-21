"""
Decision Router — Phase 6
Routes each agent to the correct intelligence tier and executes
their decision, applying wealth changes and logging results.
"""
import logging
import random
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from apps.agents.models import Agent, AgentRole
from apps.ai.rule_engine import run_rule_decision
from apps.ai.neural_model import run_neural_decision
from apps.ai.llm_pipeline import run_llm_decision
from apps.ai.models import NeuralLog

logger = logging.getLogger(__name__)

# ── Tier assignments ──────────────────────────────────────────────────────────
TIER_1_ROLES = {AgentRole.GOVERNMENT, AgentRole.INFLUENCER}
TIER_2_ROLES = {
    AgentRole.TRADER, AgentRole.INVESTOR,
    AgentRole.BUSINESS_OWNER, AgentRole.BANKER,
    AgentRole.MANUFACTURER,
}
TIER_3_ROLES = {AgentRole.CONSUMER, AgentRole.WORKER,
                AgentRole.RESEARCHER, AgentRole.RESOURCE_SUPPLIER}

# LLM timeout in seconds — non-blocking
LLM_TIMEOUT = 25.0

ACTION_WEALTH_DELTA = {}  # Empty — circulation handles wealth


def apply_wealth_change(agent, action: str, economy: dict) -> float:
    """
    Decisions no longer directly change wealth.
    The circulation engine handles all wealth transfers.
    Only panic sells assets — that's the one exception.
    """
    if action == 'panic' and agent.wealth > 50:
        # Panic sell — lose 5% as market impact
        loss = agent.wealth * 0.05
        agent.wealth = max(10.0, agent.wealth - loss)
        return -loss
    return 0.0

def run_tier1_agent(agent, economy: dict) -> dict:
    """Run LLM decision with timeout — non-blocking via thread."""
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_llm_decision, agent, economy)
            result = future.result(timeout=LLM_TIMEOUT)
            return result
    except TimeoutError:
        logger.warning(f'LLM timeout for agent {agent.id} — falling back to neural')
        return run_neural_decision(agent, economy)
    except Exception as e:
        logger.error(f'Tier 1 error agent {agent.id}: {e}')
        return {'action': 'save', 'confidence': 0.4, 'reasoning': str(e), 'tier': 1}


def log_neural_decision(agent, decision: dict, tick: int):
    """Write neural decision to NeuralLog table."""
    try:
        NeuralLog.objects.create(
            agent_id=agent.id,
            decision_input={
                'wealth': agent.wealth,
                'emotion': agent.dominant_emotion,
                'fear': agent.emotion_fear,
                'panic': agent.emotion_panic,
            },
            decision_output=decision['action'],
            confidence=decision.get('confidence', 0.0),
            reasoning=decision.get('reasoning', ''),
            tick_number=tick,
        )
    except Exception as e:
        logger.debug(f'NeuralLog write failed: {e}')


def compute_social_pressure(agent, adj: dict) -> float:
    """
    Compute social pressure score from neighbor panic/fear levels.
    Used as a neural input feature.
    """
    neighbors = adj.get(agent.id, [])
    if not neighbors:
        return 0.5
    panic_sum = sum(nb.emotion_panic + nb.emotion_fear for nb in neighbors)
    return min(1.0, panic_sum / (len(neighbors) * 2.0))


def build_neighbor_map(agents: list) -> dict:
    """Build agent_id → list of neighbor Agent objects map."""
    from apps.social.models import SocialRelationship
    from collections import defaultdict

    agent_map = {a.id: a for a in agents}
    adj = defaultdict(list)

    rels = SocialRelationship.objects.filter(
        agent_a_id__in=agent_map.keys(),
        agent_b_id__in=agent_map.keys(),
    ).values('agent_a_id', 'agent_b_id')

    for rel in rels:
        a, b = rel['agent_a_id'], rel['agent_b_id']
        if b in agent_map:
            adj[a].append(agent_map[b])
        if a in agent_map:
            adj[b].append(agent_map[a])

    return adj


def run_decision_router(context: dict) -> dict:
    tick = context['tick']
    economy = context['economy']

    agents = list(Agent.objects.filter(is_active=True))
    adj = build_neighbor_map(agents)

    tier1_agents = [a for a in agents if a.profession in TIER_1_ROLES]
    tier2_agents = [a for a in agents if a.profession in TIER_2_ROLES]
    tier3_agents = [a for a in agents if a.profession in TIER_3_ROLES]

    agent_updates = []
    decision_log = []

    # ── Tier 3 — Rule-Based ────────────────────────────────────────────────
    for agent in tier3_agents:
        decision = run_rule_decision(agent, economy)
        apply_wealth_change(agent, decision['action'], economy)
        agent.last_action = decision['action']
        agent.last_action_tick = tick
        agent_updates.append(agent)
        decision_log.append({
            'agent_id': agent.id,
            'action': decision['action'],
            'tier': 3,
        })

    # ── Tier 2 — Neural ───────────────────────────────────────────────────
    for agent in tier2_agents:
        social_pressure = compute_social_pressure(agent, adj)
        decision = run_neural_decision(agent, economy, social_pressure)
        apply_wealth_change(agent, decision['action'], economy)
        agent.last_action = decision['action']
        agent.last_action_tick = tick
        agent_updates.append(agent)
        decision_log.append({
            'agent_id': agent.id,
            'action': decision['action'],
            'confidence': decision.get('confidence', 0),
            'tier': 2,
        })
        if tick % 24 == 0:
            log_neural_decision(agent, decision, tick)

    # ── Tier 1 — LLM ──────────────────────────────────────────────────────
    if tick % 48 == 0:
        for agent in tier1_agents:
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_tier1_agent, agent, economy)
                    try:
                        decision = future.result(timeout=LLM_TIMEOUT)
                    except Exception:
                        decision = run_neural_decision(agent, economy)
            except Exception as e:
                decision = {'action': 'save', 'confidence': 0.4,
                            'reasoning': str(e), 'tier': 1}

            apply_wealth_change(agent, decision['action'], economy)
            agent.last_action = decision['action']
            agent.last_action_tick = tick
            agent_updates.append(agent)
            decision_log.append({
                'agent_id': agent.id,
                'action': decision['action'],
                'reasoning': decision.get('reasoning', '')[:100],
                'tier': 1,
            })
    else:
        for agent in tier1_agents:
            decision = run_neural_decision(agent, economy)
            apply_wealth_change(agent, decision['action'], economy)
            agent.last_action = decision['action']
            agent.last_action_tick = tick
            agent_updates.append(agent)

    # ── Bulk update ────────────────────────────────────────────────────────
    if agent_updates:
        Agent.objects.bulk_update(
            agent_updates,
            ['wealth', 'last_action', 'last_action_tick'],
        )

    context['agent_updates'] = decision_log

    if tick % 24 == 0:
        logger.info(
            f'[Tick {tick}] Decision router — '
            f'T1:{len(tier1_agents)} T2:{len(tier2_agents)} T3:{len(tier3_agents)}'
        )

    return context