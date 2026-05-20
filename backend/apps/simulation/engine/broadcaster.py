"""
Step 6: Broadcast Updates — full structured payload each tick.
Includes economy state, agent deltas, events, social influence changes.
"""
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)
BROADCAST_GROUP = 'simulation_broadcast'


def _group_send(msg_type: str, payload: dict):
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            BROADCAST_GROUP,
            {'type': msg_type, 'payload': payload},
        )
    except Exception as e:
        logger.warning(f'Broadcast failed [{msg_type}]: {e}')


def build_agent_deltas(context: dict) -> list:
    """
    Build per-agent delta list for this tick.
    Includes profession, wealth, emotion, last action.
    Sampled to max 20 agents per tick to keep payload size manageable.
    """
    from apps.agents.models import Agent
    updates = context.get('agent_updates', [])

    if not updates:
        return []

    # Get agent ids from updates
    agent_ids = [u['agent_id'] for u in updates[:20]]
    agents = {
        a.id: a for a in Agent.objects.filter(id__in=agent_ids)
    }

    deltas = []
    for update in updates[:20]:
        agent_id = update['agent_id']
        agent = agents.get(agent_id)
        if not agent:
            continue
        deltas.append({
            'agent_id': agent_id,
            'profession': agent.profession,
            'wealth': round(agent.wealth, 2),
            'dominant_emotion': agent.dominant_emotion,
            'last_action': update.get('action', agent.last_action),
            'tier': update.get('tier', 3),
            'reasoning': update.get('reasoning', ''),
        })

    return deltas


def broadcast_updates(context: dict) -> dict:
    tick = context['tick']
    eco = context['economy']

    # ── Build agent deltas ────────────────────────────────────────────────────
    agent_deltas = build_agent_deltas(context)

    # ── Main tick payload ─────────────────────────────────────────────────────
    tick_payload = {
        'type': 'tick_update',
        'tick_number': tick,
        'year': context['year'],
        'month': context['month'],
        'day': context['day'],
        'hour': context['hour'],

        # Economy
        'gdp': round(eco['gdp'], 2),
        'gdp_growth_rate': round(eco.get('gdp_growth_rate', 0.0), 4),
        'inflation': round(eco['inflation'], 4),
        'unemployment': round(eco['unemployment'], 4),
        'market_confidence': round(eco['market_confidence'], 4),
        'wealth_gini': round(eco['wealth_gini'], 4),
        'resource_index': round(eco['resource_index'], 4),
        'economic_stability': round(eco['economic_stability'], 4),
        'total_wealth': round(eco.get('total_wealth', 0), 2),

        # Agents
        'agent_deltas': agent_deltas,
        'emotion_distribution': context.get('emotion_distribution', {}),
        'behavioral_modifiers': context.get('behavioral_modifiers', {}),
        'panic_wave_active': len(context.get('panic_wave_agents', [])) > 10,

        # Resources
        'resource_shortages': context.get('resource_shortages', []),
        'resource_prices': context.get('resource_prices', {}),

        # Events
        'events': context.get('events_detected', []),

        # Social
        'herd_active': context.get('herd_active', False),

        # Policy snapshot
        'policy': context.get('policy_state', {}),
    }

    _group_send('simulation_tick', tick_payload)

    # ── Broadcast each event as a separate message ────────────────────────────
    for event in context.get('events_detected', []):
        _group_send('simulation_event', {**event, 'type': 'simulation_event'})

    return context


def broadcast_status_change(status: str, config):
    """Called from simulation views when status changes."""
    from apps.simulation.clock import format_sim_date
    payload = {
        'type': 'status_update',
        'status': status,
        'speed_multiplier': config.speed_multiplier,
        'current_tick': config.current_tick,
        'formatted_date': format_sim_date(config.current_tick),
        'current_year': config.current_year,
        'current_month': config.current_month,
        'current_day': config.current_day,
        'current_hour': config.current_hour,
    }
    _group_send('simulation_status', payload)