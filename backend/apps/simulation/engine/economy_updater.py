"""
Step 3: Update Economy — policy → resource → circulation → economy engines.
"""
import logging
from apps.economy.engine import run_economy_engine
from apps.resources.engine import run_resource_engine
from apps.policies.engine import run_policy_engine
from apps.economy.circulation import run_circulation
from apps.economy.models import EconomyState

logger = logging.getLogger(__name__)
ECONOMY_SNAPSHOT_INTERVAL = 24


def update_economy(context: dict) -> dict:
    tick = context['tick']

    # Order matters: policy → resource → circulation → economy
    context = run_policy_engine(context)
    context = run_resource_engine(context)
    context = run_circulation(context)     # NEW — money flows between agents
    context = run_economy_engine(context)

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

    return context