"""
Main simulation loop — orchestrates all engine steps for one tick.
"""
import logging
from apps.simulation.engine.observer import observe_environment
from apps.simulation.engine.agent_processor import process_agents
from apps.simulation.engine.economy_updater import update_economy
from apps.simulation.engine.social_spreader import spread_social_effects
from apps.simulation.engine.event_detector import detect_events
from apps.simulation.engine.broadcaster import broadcast_updates

logger = logging.getLogger(__name__)


def run_tick(config) -> dict:
    """
    Execute one full simulation tick in pipeline order.
    Returns the final context dict.
    """
    try:
        context = observe_environment(config)
        context = process_agents(context)
        context = update_economy(context)
        context = spread_social_effects(context)
        context = detect_events(context)
        context = broadcast_updates(context)
        logger.debug(f'[Tick {config.current_tick}] Tick complete.')
    except Exception as e:
        logger.error(f'[Tick {config.current_tick}] Tick failed: {e}', exc_info=True)
        raise

    return context