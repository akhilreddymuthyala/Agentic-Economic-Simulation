"""
Step 2: Process Agents (stub for Phase 3).
Full intelligence routing implemented in Phase 6.
"""
import logging
import random

logger = logging.getLogger(__name__)

STUB_ACTIONS = ['idle', 'buy', 'sell', 'save', 'invest', 'work', 'observe']


def process_agents(context: dict) -> dict:
    """
    Stub: assign a random last_action to a small sample of agents each tick.
    Full rule/neural/LLM routing comes in Phase 6.
    """
    tick = context['tick']

    # Only log every 24 ticks (once per sim day) to avoid noise
    if tick % 24 == 0:
        logger.info(f'[Tick {tick}] process_agents stub — '
                    f'agents will make decisions in Phase 6.')

    # Lightweight stub — randomly update 5 agents per tick
    from apps.agents.models import Agent
    sample = list(Agent.objects.filter(is_active=True).order_by('?')[:5])
    updates = []
    for agent in sample:
        agent.last_action = random.choice(STUB_ACTIONS)
        agent.last_action_tick = tick
        updates.append(agent)
        context['agent_updates'].append({
            'agent_id': agent.id,
            'action': agent.last_action,
        })

    if updates:
        Agent.objects.bulk_update(updates, ['last_action', 'last_action_tick'])

    return context