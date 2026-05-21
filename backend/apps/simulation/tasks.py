"""
Celery tasks for simulation tick scheduling.
Hardened with restart logic and stale tick detection.
"""
import logging
import time
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# Maximum ticks that can be queued before we consider the worker stalled
MAX_QUEUED_TICKS = 5


@shared_task(bind=True, max_retries=None, ignore_result=True)
def run_simulation_tick(self):
    """
    Execute one tick and schedule the next.
    Self-healing: if an error occurs, logs and reschedules rather than dying.
    """
    from apps.simulation.models import SimulationConfig, SimulationStatus
    from apps.simulation.clock import tick_interval_seconds
    from apps.simulation.engine.loop import run_tick

    try:
        config = SimulationConfig.get_active()

        if config.status != SimulationStatus.RUNNING:
            logger.info(f'Simulation {config.status} — tick scheduler stopping.')
            return

        # Advance clock
        config.advance_tick()
        config.save(update_fields=[
            'current_tick', 'current_hour', 'current_day',
            'current_week', 'current_month', 'current_year',
        ])

        # Run tick pipeline
        run_tick(config)

    except Exception as e:
        logger.error(f'Tick execution error: {e}', exc_info=True)
        # Don't crash — reschedule and continue

    finally:
        # Always reschedule next tick if simulation is still running
        try:
            config = SimulationConfig.get_active()
            if config.status == SimulationStatus.RUNNING:
                interval = tick_interval_seconds(config.speed_multiplier)
                run_simulation_tick.apply_async(countdown=interval)
        except Exception as e:
            logger.error(f'Failed to reschedule tick: {e}')


@shared_task
def verify_celery():
    logger.info('Celery worker is operational.')
    return 'Celery OK'


@shared_task
def health_check_simulation():
    """
    Periodic health check — detects and restarts stalled simulations.
    Run every 60 seconds via Celery beat.
    """
    from apps.simulation.models import SimulationConfig, SimulationStatus
    import redis
    import django.conf

    config = SimulationConfig.get_active()
    if config.status != SimulationStatus.RUNNING:
        return 'not running'

    # Check if ticks are advancing by reading last tick from Redis
    try:
        r = redis.from_url(django.conf.settings.REDIS_URL)
        last_tick_key = 'sim:health:last_tick'
        last_tick = r.get(last_tick_key)

        current_tick = str(config.current_tick).encode()

        if last_tick == current_tick:
            # Tick hasn't advanced — simulation may be stalled
            logger.warning(
                f'Health check: tick {config.current_tick} has not advanced. '
                f'Attempting restart.'
            )
            run_simulation_tick.apply_async(countdown=0)
        else:
            r.set(last_tick_key, current_tick, ex=120)

    except Exception as e:
        logger.error(f'Health check failed: {e}')

    return f'tick={config.current_tick}'