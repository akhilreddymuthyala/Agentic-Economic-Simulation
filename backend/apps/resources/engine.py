"""
Resource Engine — Phase 4
Manages supply levels and prices for food, oil, energy, housing, water.
Resource shortages drive inflation and panic.
"""
import logging
from apps.resources.models import ResourceState
from apps.policies.models import PolicyState

logger = logging.getLogger(__name__)

# Scarcity threshold — below this supply level triggers shortage events
SCARCITY_THRESHOLD = 30.0

# Price elasticity — how much price rises per unit of scarcity
PRICE_ELASTICITY = {
    'food': 0.8,
    'oil': 1.2,
    'energy': 1.0,
    'housing': 0.6,
    'water': 0.9,
}

# Natural supply recovery rate per tick (when no shortage)
RECOVERY_RATE = 0.05

# Consumption rate per tick (agents consume resources)
BASE_CONSUMPTION = {
    'food': 0.08,
    'oil': 0.06,
    'energy': 0.07,
    'housing': 0.02,
    'water': 0.05,
}


def compute_resource_price(supply: float, base_price: float, elasticity: float) -> float:
    """
    Price rises as supply falls below 100.
    At supply=100: price = base_price
    At supply=0:   price = base_price * (1 + elasticity * 5)
    """
    scarcity_factor = max(0.0, (100.0 - supply) / 100.0)
    return round(base_price * (1.0 + elasticity * scarcity_factor * 5.0), 2)


def run_resource_engine(context: dict) -> dict:
    """
    Update resource supply levels and prices each tick.
    Shortage flags are added to context for event detection.
    """
    tick = context['tick']
    policy = PolicyState.get_active()
    resource = ResourceState.get_active()

    shortages = []

    # ── Food ─────────────────────────────────────────────────────────────────
    food_consumption = BASE_CONSUMPTION['food'] * (1.0 + context['economy']['inflation'] / 100.0)
    resource.food_supply = max(0.0, min(100.0,
        resource.food_supply - food_consumption + RECOVERY_RATE
        + policy.subsidy_level * 0.001
    ))
    resource.food_price = compute_resource_price(
        resource.food_supply, 10.0, PRICE_ELASTICITY['food']
    )
    if resource.food_supply < SCARCITY_THRESHOLD:
        shortages.append({'resource': 'food', 'supply': resource.food_supply})

    # ── Oil ───────────────────────────────────────────────────────────────────
    oil_consumption = BASE_CONSUMPTION['oil'] * (1.0 + context['economy']['gdp_growth_rate'] / 100.0)
    resource.oil_supply = max(0.0, min(100.0,
        resource.oil_supply - oil_consumption + RECOVERY_RATE * 0.8
    ))
    resource.oil_price = compute_resource_price(
        resource.oil_supply, 50.0, PRICE_ELASTICITY['oil']
    )
    if resource.oil_supply < SCARCITY_THRESHOLD:
        shortages.append({'resource': 'oil', 'supply': resource.oil_supply})

    # ── Energy ────────────────────────────────────────────────────────────────
    energy_consumption = BASE_CONSUMPTION['energy']
    resource.energy_availability = max(0.0, min(100.0,
        resource.energy_availability - energy_consumption + RECOVERY_RATE * 0.9
        + policy.subsidy_level * 0.0005
    ))
    resource.energy_price = compute_resource_price(
        resource.energy_availability, 30.0, PRICE_ELASTICITY['energy']
    )
    if resource.energy_availability < SCARCITY_THRESHOLD:
        shortages.append({'resource': 'energy', 'supply': resource.energy_availability})

    # ── Housing ───────────────────────────────────────────────────────────────
    resource.housing_supply = max(0.0, min(100.0,
        resource.housing_supply - BASE_CONSUMPTION['housing'] + RECOVERY_RATE * 0.3
        + policy.government_spending * 0.000005
    ))
    resource.housing_price = compute_resource_price(
        resource.housing_supply, 200.0, PRICE_ELASTICITY['housing']
    )
    if resource.housing_supply < SCARCITY_THRESHOLD:
        shortages.append({'resource': 'housing', 'supply': resource.housing_supply})

    # ── Water ─────────────────────────────────────────────────────────────────
    resource.water_resources = max(0.0, min(100.0,
        resource.water_resources - BASE_CONSUMPTION['water'] + RECOVERY_RATE
    ))
    resource.water_price = compute_resource_price(
        resource.water_resources, 5.0, PRICE_ELASTICITY['water']
    )
    if resource.water_resources < SCARCITY_THRESHOLD:
        shortages.append({'resource': 'water', 'supply': resource.water_resources})

    resource.save()

    # Resource index = average supply
    resource_index = (
        resource.food_supply + resource.oil_supply +
        resource.energy_availability + resource.housing_supply +
        resource.water_resources
    ) / 5.0

    context['economy']['resource_index'] = round(resource_index, 4)
    context['resource_shortages'] = shortages
    context['resource_prices'] = {
        'food': resource.food_price,
        'oil': resource.oil_price,
        'energy': resource.energy_price,
        'housing': resource.housing_price,
        'water': resource.water_price,
    }

    if shortages and tick % 24 == 0:
        logger.warning(f'[Tick {tick}] Resource shortages: {[s["resource"] for s in shortages]}')

    return context