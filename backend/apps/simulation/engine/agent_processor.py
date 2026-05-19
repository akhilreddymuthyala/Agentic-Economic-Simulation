"""
Step 2: Process Agents — now calls the real decision router.
"""
import logging
from apps.ai.decision_router import run_decision_router

logger = logging.getLogger(__name__)


def process_agents(context: dict) -> dict:
    """Route all agents through their intelligence tier."""
    context = run_decision_router(context)
    return context