from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def verify_celery():
    logger.info('Celery worker is operational.')
    return 'Celery OK'