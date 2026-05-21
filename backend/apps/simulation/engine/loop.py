"""
Main simulation loop — hardened with profiling and error isolation.
Each engine step is wrapped so one failure never crashes the tick.
"""
import logging
from apps.simulation.profiler import TickProfiler
from apps.simulation.cache import cache_economy_state

logger = logging.getLogger(__name__)


def safe_step(fn, context: dict, step_name: str, profiler: TickProfiler) -> dict:
    """
    Execute one engine step safely.
    On failure: log error and return context unchanged so simulation continues.
    """
    try:
        result = fn(context)
        profiler.mark(step_name)
        return result
    except Exception as e:
        logger.error(
            f'[Tick {context.get("tick", "?")}] Step {step_name} failed: {e}',
            exc_info=True,
        )
        profiler.mark(f'{step_name}_ERROR')
        return context  # Continue with unchanged context


def run_tick(config) -> dict:
    """
    Execute one full simulation tick.
    Steps run in pipeline order with full error isolation.
    """
    from apps.simulation.engine.observer import observe_environment
    from apps.simulation.engine.agent_processor import process_agents
    from apps.simulation.engine.economy_updater import update_economy
    from apps.simulation.engine.social_spreader import spread_social_effects
    from apps.simulation.engine.event_detector import detect_events
    from apps.simulation.engine.broadcaster import broadcast_updates

    profiler = TickProfiler(config.current_tick)
    context = {}

    try:
        context = safe_step(observe_environment, {'_config': config}, 'observe', profiler)
        # observe_environment needs config passed differently
        context = observe_environment(config)
        profiler.mark('observe')
    except Exception as e:
        logger.error(f'[Tick {config.current_tick}] observe_environment failed: {e}')
        return {}

    context = safe_step(process_agents, context, 'agents', profiler)
    context = safe_step(update_economy, context, 'economy', profiler)
    context = safe_step(spread_social_effects, context, 'social', profiler)
    context = safe_step(detect_events, context, 'events', profiler)

    # Cache economy state for fast reads
    if context.get('economy'):
        cache_economy_state(context['economy'])

    context = safe_step(broadcast_updates, context, 'broadcast', profiler)

    profiler.report()
    return context