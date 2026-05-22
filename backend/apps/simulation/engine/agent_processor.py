"""
Step 2: Process Agents — decisions + employment updates.
"""
import logging
import random
from apps.ai.decision_router import run_decision_router
from apps.agents.models import Agent, AgentRole

logger = logging.getLogger(__name__)


def update_employment_status(context: dict):
    tick = context['tick']
    if tick % 12 != 0:  # Run every 12 ticks instead of 24
        return

    eco = context['economy']
    confidence = eco.get('market_confidence', 70)
    gdp_growth = eco.get('gdp_growth_rate', 0)
    gov_spending = context.get('policy_state', {}).get('government_spending', 10000)

    workers = list(Agent.objects.filter(
        profession=AgentRole.WORKER, is_active=True
    ))
    if not workers:
        return

    updates = []
    for worker in workers:
        if worker.is_employed:
            # Fire only in extreme conditions
            fire_prob = 0.0
            if confidence < 10:
                fire_prob = 0.05
            elif confidence < 25:
                fire_prob = 0.02
            if random.random() < fire_prob:
                worker.is_employed = False
                updates.append(worker)
        else:
            # LOWER hiring threshold — government spending creates jobs
            # even when confidence is low
            hire_prob = 0.0
            if gov_spending > 150000:
                hire_prob = 0.30   # High spending = aggressive hiring
            elif gov_spending > 80000:
                hire_prob = 0.20
            elif gov_spending > 30000:
                hire_prob = 0.12
            elif confidence > 30:
                hire_prob = 0.08
            elif confidence > 15:
                hire_prob = 0.04
            else:
                hire_prob = 0.02   # Always tiny chance of hiring

            if random.random() < hire_prob:
                worker.is_employed = True
                updates.append(worker)

    if updates:
        Agent.objects.bulk_update(updates, ['is_employed'])
        hired = sum(1 for w in updates if w.is_employed)
        fired = len(updates) - hired
        logger.info(f'[Tick {tick}] Employment: +{hired} hired, -{fired} fired')

def process_agents(context: dict) -> dict:
    update_employment_status(context)
    context = run_decision_router(context)
    return context