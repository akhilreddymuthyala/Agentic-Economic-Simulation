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

# Action → wealth delta mapping
ACTION_WEALTH_DELTA = {
    'buy':              lambda w, eco: -min(w * 0.05, 200),
    'sell':             lambda w, eco: w * 0.08,
    'save':             lambda w, eco: w * 0.001,
    'invest':           lambda w, eco: w * (0.1 if eco.get('market_confidence', 70) > 60 else -0.05),
    'panic':            lambda w, eco: -w * 0.15,
    'cooperate':        lambda w, eco: w * 0.02,
    'work':             lambda w, eco: random.uniform(50, 200),
    'quit':             lambda w, eco: -50,
    'raise_taxes':      lambda w, eco: 0,
    'lower_taxes':      lambda w, eco: 0,
    'stimulus':         lambda w, eco: 0,
    'regulate':         lambda w, eco: 0,
    'influence_market': lambda w, eco: w * 0.03,
    'form_alliance':    lambda w, eco: w * 0.01,
}


def apply_wealth_change(agent: Agent, action: str, economy: dict) -> float:
    """Apply wealth delta for an action. Returns delta applied."""
    delta_fn = ACTION_WEALTH_DELTA.get(action, lambda w, e: 0)
    delta = delta_fn(agent.wealth, economy)
    new_wealth = max(0.0, agent.wealth + delta)
    agent.wealth = round(new_wealth, 2)
    return delta


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
    """
    Main entry point — process all 100 agents each tick.

    Tier 3 (rule): processed synchronously in bulk — instant
    Tier 2 (neural): processed synchronously in batch — fast
    Tier 1 (LLM): processed async with timeout — non-blocking
    """
    tick = context['tick']
    economy = context['economy']

    agents = list(Agent.objects.filter(is_active=True))
    adj = build_neighbor_map(agents)

    tier1_agents = [a for a in agents if a.profession in TIER_1_ROLES]
    tier2_agents = [a for a in agents if a.profession in TIER_2_ROLES]
    tier3_agents = [a for a in agents if a.profession in TIER_3_ROLES]

    agent_updates = []
    decision_log = []

    # ── Tier 3 — Rule-Based (instant) ────────────────────────────────────────
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

    # ── Tier 2 — Neural (batch inference) ────────────────────────────────────
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
        # Log every 24 ticks to avoid DB flood
        if tick % 24 == 0:
            log_neural_decision(agent, decision, tick)

    # ── Tier 1 — LLM (fire and forget, every 24 ticks) ───────────────────────────
    
    if tick % 48 == 0:
        # Only call LLM for 3 agents per tick cycle to stay within rate limits
        # Rotate which agents get LLM vs neural fallback
        tier1_cycle_index = (tick // 24) % len(tier1_agents)
        llm_batch = tier1_agents[tier1_cycle_index:tier1_cycle_index + 3]
        neural_fallback = [a for a in tier1_agents if a not in llm_batch]

        # Neural fallback for non-LLM agents this cycle
        for agent in neural_fallback:
            decision = run_neural_decision(agent, economy)
            apply_wealth_change(agent, decision['action'], economy)
            agent.last_action = decision['action']
            agent.last_action_tick = tick
            agent_updates.append(agent)

        # LLM for the 3 selected agents — sequential not parallel
        import time
        for agent in llm_batch:
            try:
                decision = run_llm_decision(agent, economy)
                time.sleep(4)  # 4 second gap between calls = max 15/min
            except Exception as e:
                decision = run_neural_decision(agent, economy)
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

    # ── Bulk update all agents ────────────────────────────────────────────────
    if agent_updates:
        Agent.objects.bulk_update(
            agent_updates,
            ['wealth', 'last_action', 'last_action_tick'],
        )

    context['agent_updates'] = decision_log

    if tick % 24 == 0:
        tier_counts = {1: len(tier1_agents), 2: len(tier2_agents), 3: len(tier3_agents)}
        logger.info(f'[Tick {tick}] Decision router — T1:{tier_counts[1]} T2:{tier_counts[2]} T3:{tier_counts[3]}')

    return context