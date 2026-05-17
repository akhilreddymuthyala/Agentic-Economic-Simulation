"""
Step 1 of the simulation loop: Observe Environment.
Reads current economy state and agent summary into a shared context dict
that is passed through the rest of the tick pipeline.
"""
import logging
from apps.economy.models import EconomyState
from apps.agents.models import Agent
from django.db.models import Avg, Sum, Count

logger = logging.getLogger(__name__)


def observe_environment(config) -> dict:
    """
    Build and return the tick context dict.
    All subsequent engine steps read from and write to this dict.
    """
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

    agent_stats = Agent.objects.filter(is_active=True).aggregate(
        total=Count('id'),
        employed=Count('id', filter=__import__('django.db.models', fromlist=['Q']).Q(is_employed=True)),
        avg_wealth=Avg('wealth'),
        total_wealth=Sum('wealth'),
        avg_fear=Avg('emotion_fear'),
        avg_panic=Avg('emotion_panic'),
        avg_optimism=Avg('emotion_optimism'),
        avg_trust=Avg('emotion_trust'),
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
    }

    logger.debug(f'[Tick {config.current_tick}] Environment observed. '
                 f'GDP={economy_snapshot["gdp"]:.0f} '
                 f'Agents={agent_stats["total"]}')
    return context