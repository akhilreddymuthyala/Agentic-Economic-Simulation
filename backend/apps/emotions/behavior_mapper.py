"""
Behavioral Effect Mapper — Phase 5

Maps agent dominant emotions to economic behavior modifiers.
These modifiers influence agent decisions in Phase 6.
"""
from apps.agents.models import AgentEmotionState

# ── Spending multipliers by emotion ──────────────────────────────────────────
SPENDING_MULTIPLIER = {
    AgentEmotionState.NEUTRAL:    1.0,
    AgentEmotionState.FEARFUL:    0.5,    # Fear halves spending
    AgentEmotionState.GREEDY:     1.4,    # Greed boosts spending
    AgentEmotionState.TRUSTING:   1.2,    # Trust encourages spending
    AgentEmotionState.OPTIMISTIC: 1.3,    # Optimism increases spending
    AgentEmotionState.STRESSED:   0.7,    # Stress reduces spending
    AgentEmotionState.PANIC:      0.2,    # Panic near-stops spending
}

# ── Investment risk multipliers ───────────────────────────────────────────────
INVESTMENT_RISK_MULTIPLIER = {
    AgentEmotionState.NEUTRAL:    1.0,
    AgentEmotionState.FEARFUL:    0.3,
    AgentEmotionState.GREEDY:     2.0,    # Greed doubles risk appetite
    AgentEmotionState.TRUSTING:   1.3,
    AgentEmotionState.OPTIMISTIC: 1.5,
    AgentEmotionState.STRESSED:   0.6,
    AgentEmotionState.PANIC:      0.1,    # Panic kills investment
}

# ── Hiring willingness (for business owners) ──────────────────────────────────
HIRING_WILLINGNESS = {
    AgentEmotionState.NEUTRAL:    1.0,
    AgentEmotionState.FEARFUL:    0.4,
    AgentEmotionState.GREEDY:     1.2,
    AgentEmotionState.TRUSTING:   1.3,
    AgentEmotionState.OPTIMISTIC: 1.8,    # Optimism → hiring boom
    AgentEmotionState.STRESSED:   0.6,
    AgentEmotionState.PANIC:      0.1,
}

# ── Cooperation rate modifiers ────────────────────────────────────────────────
COOPERATION_MODIFIER = {
    AgentEmotionState.NEUTRAL:    1.0,
    AgentEmotionState.FEARFUL:    0.6,
    AgentEmotionState.GREEDY:     0.7,
    AgentEmotionState.TRUSTING:   1.8,    # Trust maximises cooperation
    AgentEmotionState.OPTIMISTIC: 1.3,
    AgentEmotionState.STRESSED:   0.7,
    AgentEmotionState.PANIC:      0.3,
}

# ── Sell pressure (used for market decisions) ─────────────────────────────────
SELL_PRESSURE = {
    AgentEmotionState.NEUTRAL:    0.3,
    AgentEmotionState.FEARFUL:    0.6,
    AgentEmotionState.GREEDY:     0.2,
    AgentEmotionState.TRUSTING:   0.2,
    AgentEmotionState.OPTIMISTIC: 0.15,
    AgentEmotionState.STRESSED:   0.5,
    AgentEmotionState.PANIC:      0.95,   # Panic triggers mass selling
}


def get_behavior_modifiers(dominant_emotion: str) -> dict:
    """Return all behavior multipliers for a given dominant emotion."""
    return {
        'spending_multiplier':      SPENDING_MULTIPLIER.get(dominant_emotion, 1.0),
        'investment_risk':          INVESTMENT_RISK_MULTIPLIER.get(dominant_emotion, 1.0),
        'hiring_willingness':       HIRING_WILLINGNESS.get(dominant_emotion, 1.0),
        'cooperation_modifier':     COOPERATION_MODIFIER.get(dominant_emotion, 1.0),
        'sell_pressure':            SELL_PRESSURE.get(dominant_emotion, 0.3),
    }


def apply_behavioral_effects(context: dict) -> dict:
    """
    Compute society-wide average behavioral modifiers from agent emotion distribution.
    Feeds into economy engine to adjust GDP, confidence, and unemployment.
    """
    from apps.agents.models import Agent
    from django.db.models import Avg, Count

    emotion_dist = (
        Agent.objects
        .filter(is_active=True)
        .values('dominant_emotion')
        .annotate(count=Count('id'))
    )

    total_agents = sum(e['count'] for e in emotion_dist)
    if total_agents == 0:
        return context

    # Weighted average of each modifier across all agents
    weighted_spending = 0.0
    weighted_investment = 0.0
    weighted_hiring = 0.0
    weighted_cooperation = 0.0
    weighted_sell_pressure = 0.0

    for entry in emotion_dist:
        em = entry['dominant_emotion']
        weight = entry['count'] / total_agents
        mods = get_behavior_modifiers(em)
        weighted_spending += mods['spending_multiplier'] * weight
        weighted_investment += mods['investment_risk'] * weight
        weighted_hiring += mods['hiring_willingness'] * weight
        weighted_cooperation += mods['cooperation_modifier'] * weight
        weighted_sell_pressure += mods['sell_pressure'] * weight

    # Apply behavioral effects to economy context
    eco = context['economy']

    # High sell pressure → drops market confidence
    sell_confidence_impact = (weighted_sell_pressure - 0.3) * -20.0
    eco['market_confidence'] = max(0.0, min(100.0,
        eco['market_confidence'] + sell_confidence_impact
    ))

    # Low spending multiplier → reduces GDP
    spending_gdp_impact = (weighted_spending - 1.0) * eco['gdp'] * 0.001
    eco['gdp'] = max(10000.0, eco['gdp'] + spending_gdp_impact)

    # Hiring willingness affects unemployment
    hiring_unemployment_impact = (1.0 - weighted_hiring) * 0.5
    eco['unemployment'] = max(0.0, min(100.0,
        eco['unemployment'] + hiring_unemployment_impact
    ))

    context['economy'] = eco
    context['behavioral_modifiers'] = {
        'spending_multiplier': round(weighted_spending, 3),
        'investment_risk': round(weighted_investment, 3),
        'hiring_willingness': round(weighted_hiring, 3),
        'cooperation_modifier': round(weighted_cooperation, 3),
        'sell_pressure': round(weighted_sell_pressure, 3),
    }

    return context