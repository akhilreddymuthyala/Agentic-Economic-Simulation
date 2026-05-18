"""
Step 3: Update Economy — now calls the real economy, resource, and policy engines.
"""
import logging
from apps.economy.engine import run_economy_engine
from apps.resources.engine import run_resource_engine
from apps.policies.engine import run_policy_engine
from apps.economy.models import EconomyState

logger = logging.getLogger(__name__)

ECONOMY_SNAPSHOT_INTERVAL = 24  # once per sim day


def update_economy(context: dict) -> dict:
    tick = context['tick']

    # Run engines in order: policy → resource → economy
    context = run_policy_engine(context)
    context = run_resource_engine(context)
    context = run_economy_engine(context)

    # Write snapshot to DB once per sim day
    if tick % ECONOMY_SNAPSHOT_INTERVAL == 0:
        eco = context['economy']
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
        logger.debug(f'[Tick {tick}] Economy snapshot saved.')

    return context