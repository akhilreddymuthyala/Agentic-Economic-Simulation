"""
Economy Engine — Phase 4
Calculates GDP, inflation, unemployment, market confidence,
wealth distribution (Gini), resource index, and economic stability
each tick based on agent states, transactions, policies, and resources.
"""
import logging
from django.db.models import Sum, Avg, Count, Q
from apps.agents.models import Agent, AgentRole
from apps.economy.models import EconomyState, Transaction
from apps.policies.models import PolicyState
from apps.resources.models import ResourceState

logger = logging.getLogger(__name__)

# How many ticks to look back when computing transaction-based GDP
GDP_WINDOW_TICKS = 24  # 1 sim day


def compute_gini(wealth_list: list) -> float:
    """Compute Gini coefficient from a list of wealth values."""
    if not wealth_list or len(wealth_list) < 2:
        return 0.0
    sorted_w = sorted(wealth_list)
    n = len(sorted_w)
    total = sum(sorted_w)
    if total == 0:
        return 0.0
    cumulative = 0.0
    gini_sum = 0.0
    for i, w in enumerate(sorted_w):
        cumulative += w
        gini_sum += (2 * (i + 1) - n - 1) * w
    return gini_sum / (n * total)


def calculate_gdp(tick: int, base_gdp: float, policy: PolicyState) -> float:
    """
    GDP = base transaction volume over last window
          + government spending injection
          - tax drag
    """
    window_start = max(0, tick - GDP_WINDOW_TICKS)
    transaction_volume = Transaction.objects.filter(
        tick_number__gte=window_start,
        tick_number__lte=tick,
    ).aggregate(total=Sum('amount'))['total'] or 0.0

    # Scale transaction volume to GDP magnitude
    gdp_from_transactions = transaction_volume * 10.0

    # Government spending adds to GDP (Keynesian multiplier ~1.5)
    gov_contribution = policy.government_spending * 1.5

    # Tax reduces private sector activity
    tax_drag = base_gdp * (policy.tax_rate / 100) * 0.1

    # Subsidy boosts production
    subsidy_boost = policy.subsidy_level * 0.5

    raw_gdp = base_gdp + gdp_from_transactions + gov_contribution + subsidy_boost - tax_drag

    # Clamp to realistic range
    return max(10000.0, min(10_000_000.0, raw_gdp))


def calculate_inflation(current_inflation: float, policy: PolicyState,
                        resource: ResourceState, money_supply: float,
                        prev_money_supply: float) -> float:
    """
    Inflation driven by:
    - Money supply growth (quantity theory)
    - Interest rate (higher rate = lower inflation)
    - Resource scarcity (cost-push)
    - Government spending (demand-pull)
    """
    # Money supply growth pressure
    money_growth = 0.0
    if prev_money_supply > 0:
        money_growth = (money_supply - prev_money_supply) / prev_money_supply
    money_pressure = money_growth * 50.0

    # Interest rate dampens inflation
    interest_dampener = -(policy.interest_rate - 5.0) * 0.05

    # Resource scarcity pushes inflation up
    avg_supply = (
        resource.food_supply + resource.oil_supply +
        resource.energy_availability + resource.water_resources
    ) / 4.0
    scarcity_pressure = max(0.0, (100.0 - avg_supply) / 100.0) * 0.5

    # Government overspending = demand-pull inflation
    spending_pressure = max(0.0, (policy.government_spending - 10000.0) / 100000.0) * 0.3

    # Stimulus is a direct injection
    stimulus_pressure = 0.2 if policy.stimulus_active else 0.0

    delta = money_pressure + interest_dampener + scarcity_pressure + spending_pressure + stimulus_pressure

    # Mean-revert toward 2% target slowly
    reversion = (2.0 - current_inflation) * 0.01

    new_inflation = current_inflation + delta + reversion
    return max(0.0, min(50.0, new_inflation))


def calculate_unemployment(current_unemployment: float, policy: PolicyState,
                           gdp: float, prev_gdp: float) -> float:
    """
    Unemployment driven by:
    - GDP growth (Okun's law: +1% GDP growth → -0.5% unemployment)
    - Interest rate (higher = less business investment = more unemployment)
    - Government spending (job creation)
    - Stimulus
    """
    gdp_growth = 0.0
    if prev_gdp > 0:
        gdp_growth = (gdp - prev_gdp) / prev_gdp * 100.0

    okun_effect = -gdp_growth * 0.5
    interest_effect = (policy.interest_rate - 5.0) * 0.05
    spending_effect = -(policy.government_spending / 100000.0) * 0.3
    stimulus_effect = -0.15 if policy.stimulus_active else 0.0

    # Natural rate reversion toward 5%
    reversion = (5.0 - current_unemployment) * 0.005

    delta = okun_effect + interest_effect + spending_effect + stimulus_effect + reversion
    new_unemployment = current_unemployment + delta

    # Count actual unemployed agents
    total_workers = Agent.objects.filter(
        profession__in=[AgentRole.WORKER, AgentRole.CONSUMER],
        is_active=True,
    ).count()
    unemployed = Agent.objects.filter(
        profession__in=[AgentRole.WORKER, AgentRole.CONSUMER],
        is_active=True,
        is_employed=False,
    ).count()

    if total_workers > 0:
        agent_unemployment = (unemployed / total_workers) * 100.0
        # Blend model and agent-based unemployment
        new_unemployment = new_unemployment * 0.7 + agent_unemployment * 0.3

    return max(0.0, min(100.0, new_unemployment))


def calculate_market_confidence(current_confidence: float, policy: PolicyState,
                                avg_optimism: float, avg_fear: float,
                                avg_panic: float, gdp_growth: float) -> float:
    """
    Market confidence driven by:
    - Agent emotions (optimism raises, fear/panic drops)
    - GDP growth
    - Interest rate stability
    - Policy regulation
    """
    emotion_effect = (avg_optimism - avg_fear - avg_panic * 2.0) * 20.0
    gdp_effect = gdp_growth * 2.0
    regulation_effect = (policy.market_regulation - 50.0) * 0.05
    stimulus_effect = 3.0 if policy.stimulus_active else 0.0

    # Revert toward 70 baseline
    reversion = (70.0 - current_confidence) * 0.02

    delta = emotion_effect + gdp_effect + regulation_effect + stimulus_effect + reversion
    new_confidence = current_confidence + delta
    return max(0.0, min(100.0, new_confidence))


def calculate_economic_stability(gdp: float, inflation: float,
                                 unemployment: float, confidence: float,
                                 gini: float) -> float:
    """
    Composite stability score 0–100.
    High inflation, unemployment, inequality, low confidence = low stability.
    """
    inflation_penalty = max(0.0, inflation - 2.0) * 2.0
    unemployment_penalty = max(0.0, unemployment - 5.0) * 1.5
    inequality_penalty = gini * 30.0
    confidence_bonus = confidence * 0.3

    stability = 100.0 - inflation_penalty - unemployment_penalty - inequality_penalty + confidence_bonus
    return max(0.0, min(100.0, stability))


def run_economy_engine(context: dict) -> dict:
    """
    Main entry point called by the simulation loop each tick.
    Updates context['economy'] with freshly computed values.
    """
    tick = context['tick']
    eco = context['economy']
    agent_stats = context['agent_stats']

    policy = PolicyState.get_active()
    resource = ResourceState.get_active()

    prev_gdp = eco['gdp']
    prev_money_supply = eco['total_money_supply']

    # ── GDP ───────────────────────────────────────────────────────────────────
    new_gdp = calculate_gdp(tick, prev_gdp, policy)
    gdp_growth = ((new_gdp - prev_gdp) / prev_gdp * 100.0) if prev_gdp > 0 else 0.0

    # ── Money supply: total agent wealth ─────────────────────────────────────
    total_wealth = agent_stats.get('total_wealth') or eco['total_wealth']
    new_money_supply = total_wealth + policy.government_spending

    # ── Inflation ─────────────────────────────────────────────────────────────
    new_inflation = calculate_inflation(
        eco['inflation'], policy, resource,
        new_money_supply, prev_money_supply,
    )

    # ── Unemployment ─────────────────────────────────────────────────────────
    new_unemployment = calculate_unemployment(
        eco['unemployment'], policy, new_gdp, prev_gdp,
    )

    # ── Gini coefficient ─────────────────────────────────────────────────────
    wealth_values = list(
        Agent.objects.filter(is_active=True).values_list('wealth', flat=True)
    )
    new_gini = compute_gini(wealth_values)

    # ── Market confidence ─────────────────────────────────────────────────────
    new_confidence = calculate_market_confidence(
        eco['market_confidence'], policy,
        avg_optimism=agent_stats.get('avg_optimism') or 0.5,
        avg_fear=agent_stats.get('avg_fear') or 0.0,
        avg_panic=agent_stats.get('avg_panic') or 0.0,
        gdp_growth=gdp_growth,
    )

    # ── Resource index ────────────────────────────────────────────────────────
    resource_index = (
        resource.food_supply + resource.oil_supply +
        resource.energy_availability + resource.housing_supply +
        resource.water_resources
    ) / 5.0

    # ── Economic stability ────────────────────────────────────────────────────
    new_stability = calculate_economic_stability(
        new_gdp, new_inflation, new_unemployment, new_confidence, new_gini,
    )

    # ── Update context ────────────────────────────────────────────────────────
    context['economy'] = {
        'gdp': round(new_gdp, 2),
        'gdp_growth_rate': round(gdp_growth, 4),
        'inflation': round(new_inflation, 4),
        'unemployment': round(new_unemployment, 4),
        'market_confidence': round(new_confidence, 4),
        'wealth_gini': round(new_gini, 4),
        'resource_index': round(resource_index, 4),
        'economic_stability': round(new_stability, 4),
        'total_money_supply': round(new_money_supply, 2),
        'total_wealth': round(total_wealth, 2),
    }

    if tick % 24 == 0:
        logger.info(
            f'[Tick {tick}] Economy — GDP={new_gdp:.0f} '
            f'Inflation={new_inflation:.2f}% '
            f'Unemployment={new_unemployment:.2f}% '
            f'Confidence={new_confidence:.1f}'
        )

    return context