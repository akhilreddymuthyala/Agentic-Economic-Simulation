"""
Step 2: Process Agents — decisions + employment updates.
"""
import logging
import random
from apps.ai.decision_router import run_decision_router
from apps.agents.models import Agent, AgentRole

logger = logging.getLogger(__name__)


def update_employment_status(context: dict):
    """
    Update worker employment status based on economy.
    Business owners hire/fire based on market confidence and GDP growth.
    """
    tick = context['tick']
    if tick % 24 != 0:  # Only update once per sim day
        return

    eco = context['economy']
    confidence = eco.get('market_confidence', 70)
    gdp_growth = eco.get('gdp_growth_rate', 0)

    workers = list(Agent.objects.filter(
        profession=AgentRole.WORKER, is_active=True
    ))
    if not workers:
        return

    updates = []
    for worker in workers:
        if worker.is_employed:
            # Risk of being fired when economy is bad
            fire_prob = 0.0
            if confidence < 30:
                fire_prob = 0.15
            elif confidence < 50:
                fire_prob = 0.05
            elif gdp_growth < -1.0:
                fire_prob = 0.08

            if random.random() < fire_prob:
                worker.is_employed = False
                updates.append(worker)
        else:
            # Chance of getting hired when economy is good
            hire_prob = 0.0
            if confidence > 70:
                hire_prob = 0.20
            elif confidence > 55:
                hire_prob = 0.10
            elif gdp_growth > 0.5:
                hire_prob = 0.08

            if random.random() < hire_prob:
                worker.is_employed = True
                updates.append(worker)

    if updates:
        Agent.objects.bulk_update(updates, ['is_employed'])
        logger.debug(f'[Tick {tick}] Employment updated: {len(updates)} workers')


def process_agents(context: dict) -> dict:
    update_employment_status(context)
    context = run_decision_router(context)
    return context