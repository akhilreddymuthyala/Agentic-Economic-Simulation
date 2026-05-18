"""
Step 6: Broadcast Updates — now includes emotion distribution and behavioral modifiers.
"""
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)
BROADCAST_GROUP = 'simulation_broadcast'


def broadcast_updates(context: dict) -> dict:
    tick = context['tick']
    eco = context['economy']

    payload = {
        'type': 'tick_update',
        'tick_number': tick,
        'year': context['year'],
        'month': context['month'],
        'day': context['day'],
        'hour': context['hour'],
        'gdp': round(eco['gdp'], 2),
        'gdp_growth_rate': round(eco.get('gdp_growth_rate', 0.0), 4),
        'inflation': round(eco['inflation'], 4),
        'unemployment': round(eco['unemployment'], 4),
        'market_confidence': round(eco['market_confidence'], 4),
        'wealth_gini': round(eco['wealth_gini'], 4),
        'resource_index': round(eco['resource_index'], 4),
        'economic_stability': round(eco['economic_stability'], 4),
        'agent_updates': context.get('agent_updates', []),
        'events': context.get('events_detected', []),
        'emotion_distribution': context.get('emotion_distribution', {}),
        'behavioral_modifiers': context.get('behavioral_modifiers', {}),
        'panic_wave_active': len(context.get('panic_wave_agents', [])) > 10,
        'resource_shortages': context.get('resource_shortages', []),
        'resource_prices': context.get('resource_prices', {}),
    }

    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            BROADCAST_GROUP,
            {'type': 'simulation_tick', 'payload': payload},
        )
    except Exception as e:
        logger.warning(f'[Tick {tick}] Broadcast failed: {e}')

    return context