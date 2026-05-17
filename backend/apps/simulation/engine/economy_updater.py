"""
Step 3: Update Economy (stub for Phase 3).
Full economy calculations implemented in Phase 4.
"""
import logging
import random
from apps.economy.models import EconomyState

logger = logging.getLogger(__name__)

# How often (in ticks) to write an economy snapshot
ECONOMY_SNAPSHOT_INTERVAL = 24  # once per sim day


def update_economy(context: dict) -> dict:
    """
    Stub: apply tiny random drift to economy metrics each tick.
    Full engine implemented in Phase 4.
    """
    tick = context['tick']
    eco = context['economy']

    # Small random drift so metrics visibly change
    eco['gdp'] = max(0, eco['gdp'] * (1 + random.uniform(-0.0001, 0.0002)))
    eco['inflation'] = max(0, min(50, eco['inflation'] + random.uniform(-0.01, 0.02)))
    eco['market_confidence'] = max(0, min(100, eco['market_confidence'] + random.uniform(-0.1, 0.1)))
    eco['unemployment'] = max(0, min(100, eco['unemployment'] + random.uniform(-0.05, 0.05)))
    eco['economic_stability'] = max(0, min(100, eco['economic_stability'] + random.uniform(-0.05, 0.05)))

    # Write a snapshot to DB every ECONOMY_SNAPSHOT_INTERVAL ticks
    if tick % ECONOMY_SNAPSHOT_INTERVAL == 0:
        EconomyState.objects.create(
            gdp=eco['gdp'],
            gdp_growth_rate=eco['gdp_growth_rate'],
            inflation=eco['inflation'],
            unemployment=eco['unemployment'],
            market_confidence=eco['market_confidence'],
            wealth_gini=eco['wealth_gini'],
            resource_index=eco['resource_index'],
            economic_stability=eco['economic_stability'],
            total_money_supply=eco['total_money_supply'],
            total_wealth=eco['total_wealth'],
            tick_number=tick,
            simulation_hour=context['hour'],
            simulation_day=context['day'],
            simulation_month=context['month'],
            simulation_year=context['year'],
        )
        logger.debug(f'[Tick {tick}] Economy snapshot saved. GDP={eco["gdp"]:.0f}')

    context['economy'] = eco
    return context