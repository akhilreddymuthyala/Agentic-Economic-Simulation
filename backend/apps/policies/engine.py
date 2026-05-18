"""
Policy Engine — Phase 4
Applies active policies to the economy each tick.
Validates policy bounds and computes direct effects.
"""
import logging
from apps.policies.models import PolicyState

logger = logging.getLogger(__name__)

# Policy effect coefficients
TAX_GDP_MULTIPLIER = -0.0008       # Each 1% tax reduces GDP by 0.08%
SPENDING_GDP_MULTIPLIER = 0.00015  # Each unit of spending adds to GDP
INTEREST_INFLATION_COEFF = -0.05   # Higher interest → lower inflation
SUBSIDY_SUPPLY_BOOST = 0.002       # Subsidies restore resource supply


def apply_stimulus(context: dict, policy: PolicyState) -> dict:
    """If stimulus is active, inject money into agent wealth."""
    if not policy.stimulus_active or policy.stimulus_amount <= 0:
        return context

    from apps.agents.models import Agent, AgentRole
    # Distribute stimulus equally to consumers and workers
    recipients = Agent.objects.filter(
        profession__in=[AgentRole.CONSUMER, AgentRole.WORKER],
        is_active=True,
    )
    count = recipients.count()
    if count == 0:
        return context

    per_agent = policy.stimulus_amount / count

    agents_to_update = []
    for agent in recipients:
        agent.wealth = round(agent.wealth + per_agent, 2)
        agents_to_update.append(agent)

    Agent.objects.bulk_update(agents_to_update, ['wealth'])
    logger.info(f'[Tick {context["tick"]}] Stimulus distributed: '
                f'${per_agent:.2f} to {count} agents.')

    return context


def run_policy_engine(context: dict) -> dict:
    """
    Apply policy effects to the economy context.
    Called once per tick before economy engine finalises numbers.
    """
    tick = context['tick']
    policy = PolicyState.get_active()
    eco = context['economy']

    # Tax effect on GDP (already handled in economy engine but log it)
    tax_effect = eco['gdp'] * policy.tax_rate * TAX_GDP_MULTIPLIER

    # Government spending effect
    spending_effect = policy.government_spending * SPENDING_GDP_MULTIPLIER

    # Interest rate effect on inflation (already in economy engine)
    interest_effect = (policy.interest_rate - 5.0) * INTEREST_INFLATION_COEFF

    # Apply stimulus if active
    context = apply_stimulus(context, policy)

    # Store policy snapshot in context for broadcasting
    context['policy_state'] = {
        'tax_rate': policy.tax_rate,
        'interest_rate': policy.interest_rate,
        'government_spending': policy.government_spending,
        'subsidy_level': policy.subsidy_level,
        'stimulus_active': policy.stimulus_active,
        'stimulus_amount': policy.stimulus_amount,
        'market_regulation': policy.market_regulation,
    }

    if tick % 24 == 0:
        logger.info(
            f'[Tick {tick}] Policy — Tax={policy.tax_rate}% '
            f'Interest={policy.interest_rate}% '
            f'Spending={policy.government_spending:.0f} '
            f'Stimulus={policy.stimulus_active}'
        )

    return context