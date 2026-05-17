"""
Celery tasks for the simulation tick scheduler.
The tick task fires itself recursively using countdown,
respecting the current speed multiplier.
"""
import logging
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=None, ignore_result=True)
def run_simulation_tick(self):
    """
    Execute one simulation tick and schedule the next one.
    Self-rescheduling pattern — no beat schedule needed.
    """
    from apps.simulation.models import SimulationConfig, SimulationStatus
    from apps.simulation.clock import tick_interval_seconds
    from apps.simulation.engine.loop import run_tick

    config = SimulationConfig.get_active()

    if config.status != SimulationStatus.RUNNING:
        logger.info(f'Simulation is {config.status}. Tick scheduler stopped.')
        return

    # Advance the clock
    config.advance_tick()
    config.save(update_fields=[
        'current_tick', 'current_hour', 'current_day',
        'current_week', 'current_month', 'current_year',
    ])

    # Run the engine pipeline
    run_tick(config)

    # Schedule next tick
    interval = tick_interval_seconds(config.speed_multiplier)
    run_simulation_tick.apply_async(countdown=interval)


@shared_task
def verify_celery():
    logger.info('Celery worker is operational.')
    return 'Celery OK'