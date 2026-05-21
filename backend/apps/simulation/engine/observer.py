"""
Step 1: Observe Environment.
Reads economy and agent stats into the tick context dict.
Uses Redis cache to avoid hitting DB on every single tick.
"""
import logging
from django.db.models import Avg, Sum, Count, Q
from apps.agents.models import Agent
from apps.economy.models import EconomyState
from apps.simulation.cache import get_cached_economy_state

logger = logging.getLogger(__name__)


def observe_environment(config) -> dict:
    """Build and return the tick context dict."""

    # Try cache first for economy state
    cached_eco = get_cached_economy_state()

    if cached_eco:
        economy_snapshot = cached_eco
    else:
        latest_economy = EconomyState.get_latest()
        if latest_economy:
            economy_snapshot = {
                'gdp': latest_economy.gdp,
                'gdp_growth_rate': latest_economy.gdp_growth_rate,
                'inflation': latest_economy.inflation,
                'unemployment': latest_economy.unemployment,
                'market_confidence': latest_economy.market_confidence,
                'wealth_gini': latest_economy.wealth_gini,
                'resource_index': latest_economy.resource_index,
                'economic_stability': latest_economy.economic_stability,
                'total_money_supply': latest_economy.total_money_supply,
                'total_wealth': latest_economy.total_wealth,
            }
        else:
            economy_snapshot = EconomyState.get_initial()

    # Agent stats — optimized single query
    agent_stats = Agent.objects.filter(is_active=True).aggregate(
        total=Count('id'),
        employed=Count('id', filter=Q(is_employed=True)),
        avg_wealth=Avg('wealth'),
        total_wealth=Sum('wealth'),
        avg_fear=Avg('emotion_fear'),
        avg_panic=Avg('emotion_panic'),
        avg_optimism=Avg('emotion_optimism'),
        avg_trust=Avg('emotion_trust'),
        avg_stress=Avg('emotion_stress'),
        avg_greed=Avg('emotion_greed'),
    )

    context = {
        'tick': config.current_tick,
        'year': config.current_year,
        'month': config.current_month,
        'day': config.current_day,
        'hour': config.current_hour,
        'speed': config.speed_multiplier,
        'economy': economy_snapshot,
        'agent_stats': agent_stats,
        'events_detected': [],
        'agent_updates': [],
        'resource_shortages': [],
        'resource_prices': {},
        'policy_state': {},
        'panic_wave_agents': [],
        'herd_active': False,
        'behavioral_modifiers': {},
        'emotion_distribution': {},
    }

    logger.debug(
        f'[Tick {config.current_tick}] Observed: '
        f'GDP={economy_snapshot["gdp"]:.0f} '
        f'Agents={agent_stats["total"]}'
    )
    return context