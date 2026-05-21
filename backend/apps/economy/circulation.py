"""
Money Circulation Engine
Handles wealth transfers between agent roles each tick:
- Consumers/Workers pay Business Owners for goods
- Business Owners pay Workers wages
- Government collects taxes and pays government agents
- Bankers earn interest on loans
- Traders/Investors earn from market activity
- Manufacturers earn from production
"""
import logging
import random
from django.db.models import Avg, Sum
from apps.agents.models import Agent, AgentRole

from apps.simulation.tuning import (
    WAGE_RATE,
    CONSUMER_SPEND_RATE,
    TAX_COLLECTION_RATE,
    CIRCULATION_INTERVAL,
)

logger = logging.getLogger(__name__)

BANKER_INTEREST_RATE = 0.001
TRADER_MARKET_RATE = 0.005
MANUFACTURER_PRODUCTION_RATE = 0.003
RESOURCE_CONSUMPTION_RATE = 0.002


def run_circulation(context: dict) -> dict:
    """
    Simulate money flowing between agent classes each tick.
    This is the core of economic circulation.
    """
    tick = context['tick']
    eco = context['economy']
    policy = context.get('policy_state', {})
    tax_rate = policy.get('tax_rate', 20.0) / 100.0

    # Only run full circulation every 6 ticks for performance
    if tick % 6 != 0:
        return context

    agents_by_role = {}
    all_agents = list(Agent.objects.filter(is_active=True))
    for agent in all_agents:
        agents_by_role.setdefault(agent.profession, []).append(agent)

    updates = []

    consumers = agents_by_role.get(AgentRole.CONSUMER, [])
    workers = agents_by_role.get(AgentRole.WORKER, [])
    business_owners = agents_by_role.get(AgentRole.BUSINESS_OWNER, [])
    manufacturers = agents_by_role.get(AgentRole.MANUFACTURER, [])
    government_agents = agents_by_role.get(AgentRole.GOVERNMENT, [])
    bankers = agents_by_role.get(AgentRole.BANKER, [])
    traders = agents_by_role.get(AgentRole.TRADER, [])
    investors = agents_by_role.get(AgentRole.INVESTOR, [])
    researchers = agents_by_role.get(AgentRole.RESEARCHER, [])
    influencers = agents_by_role.get(AgentRole.INFLUENCER, [])
    resource_suppliers = agents_by_role.get(AgentRole.RESOURCE_SUPPLIER, [])

    # ── 1. Workers earn wages from Business Owners ─────────────────────────
    if business_owners and workers:
        total_business_wealth = sum(b.wealth for b in business_owners)
        wage_pool = total_business_wealth * WAGE_RATE
        per_worker_wage = wage_pool / len(workers) if workers else 0

        for biz in business_owners:
            pay = biz.wealth * WAGE_RATE
            biz.wealth = max(100.0, biz.wealth - pay)
            updates.append(biz)

        for worker in workers:
            if worker.is_employed:
                worker.wealth += per_worker_wage
                updates.append(worker)

    # ── 2. Consumers spend on goods → Business Owners earn ────────────────
    if consumers and business_owners:
        total_consumer_spend = 0
        for consumer in consumers:
            spend = consumer.wealth * CONSUMER_SPEND_RATE
            # Scale by emotion: panic reduces spend, optimism increases
            emotion_multiplier = {
                'panic': 0.1, 'fearful': 0.4, 'stressed': 0.6,
                'neutral': 1.0, 'optimistic': 1.3, 'trusting': 1.2,
                'greedy': 1.5,
            }.get(consumer.dominant_emotion, 1.0)
            spend = spend * emotion_multiplier
            spend = min(spend, consumer.wealth * 0.3)  # cap at 30% wealth
            consumer.wealth = max(10.0, consumer.wealth - spend)
            total_consumer_spend += spend
            updates.append(consumer)

        # Distribute consumer spending to business owners proportionally
        per_biz = total_consumer_spend / len(business_owners)
        for biz in business_owners:
            biz.wealth += per_biz
            if biz not in updates:
                updates.append(biz)

    # ── 3. Tax collection → Government agents ─────────────────────────────
    if government_agents:
        total_tax = 0
        taxable_agents = [
            a for a in all_agents
            if a.profession not in {AgentRole.GOVERNMENT, AgentRole.CONSUMER}
        ]
        for agent in taxable_agents:
            tax = agent.wealth * tax_rate * TAX_COLLECTION_RATE
            agent.wealth = max(10.0, agent.wealth - tax)
            total_tax += tax
            if agent not in updates:
                updates.append(agent)

        per_gov = total_tax / len(government_agents)
        for gov in government_agents:
            gov.wealth += per_gov
            if gov not in updates:
                updates.append(gov)

    # ── 4. Bankers earn interest ───────────────────────────────────────────
    for banker in bankers:
        # Bankers earn from all agents proportional to market activity
        interest_income = sum(
            a.wealth * BANKER_INTEREST_RATE
            for a in workers + consumers
            if a.wealth > 500
        ) / max(len(bankers), 1)
        banker.wealth += interest_income
        if banker not in updates:
            updates.append(banker)

    # ── 5. Traders and Investors earn from market volatility ──────────────
    market_vol = abs(eco.get('gdp_growth_rate', 0)) + eco.get('inflation', 2) / 100
    for trader in traders + investors:
        # Traders profit from volatility
        profit = trader.wealth * TRADER_MARKET_RATE * (1 + market_vol)
        # But also risk loss in crashes
        if eco.get('market_confidence', 70) < 40:
            profit = -trader.wealth * 0.02
        trader.wealth = max(10.0, trader.wealth + profit)
        if trader not in updates:
            updates.append(trader)

    # ── 6. Manufacturers earn from production ─────────────────────────────
    resource_idx = eco.get('resource_index', 100) / 100.0
    for mfr in manufacturers:
        production_income = mfr.wealth * MANUFACTURER_PRODUCTION_RATE * resource_idx
        mfr.wealth += production_income
        if mfr not in updates:
            updates.append(mfr)

    # ── 7. Researchers earn innovation income ─────────────────────────────
    for researcher in researchers:
        gdp_growth = eco.get('gdp_growth_rate', 0)
        innovation_income = researcher.wealth * 0.004 * max(1, gdp_growth / 10)
        researcher.wealth += innovation_income
        if researcher not in updates:
            updates.append(researcher)

    # ── 8. Influencers earn from social capital ────────────────────────────
    for influencer in influencers:
        social_income = influencer.wealth * 0.003
        influencer.wealth += social_income
        if influencer not in updates:
            updates.append(influencer)

    # ── 9. Resource suppliers earn from resource scarcity ─────────────────
    shortages = context.get('resource_shortages', [])
    shortage_bonus = 1.0 + len(shortages) * 0.5
    for supplier in resource_suppliers:
        supply_income = supplier.wealth * RESOURCE_CONSUMPTION_RATE * shortage_bonus
        supplier.wealth += supply_income
        if supplier not in updates:
            updates.append(supplier)

    # ── Bulk update ────────────────────────────────────────────────────────
    if updates:
        # Deduplicate
        seen = set()
        unique_updates = []
        for a in updates:
            if a.id not in seen:
                seen.add(a.id)
                unique_updates.append(a)

        Agent.objects.bulk_update(unique_updates, ['wealth'])

        if tick % 24 == 0:
            total_w = sum(a.wealth for a in unique_updates)
            logger.info(f'[Tick {tick}] Circulation — {len(unique_updates)} agents updated, '
                        f'total wealth flowing: ${total_w:.0f}')

    return context