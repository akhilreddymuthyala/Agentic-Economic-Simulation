"""
Redis caching for frequently read simulation state.
Reduces DB queries on hot paths like economy state reads per tick.
"""
import json
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

ECONOMY_CACHE_KEY = 'sim:economy:latest'
CONFIG_CACHE_KEY = 'sim:config:active'
AGENT_STATS_CACHE_KEY = 'sim:agents:stats'
CACHE_TTL = 5  # seconds — short TTL so data stays fresh


def cache_economy_state(eco_dict: dict):
    try:
        cache.set(ECONOMY_CACHE_KEY, json.dumps(eco_dict), CACHE_TTL)
    except Exception as e:
        logger.debug(f'Cache write failed: {e}')


def get_cached_economy_state() -> dict | None:
    try:
        raw = cache.get(ECONOMY_CACHE_KEY)
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.debug(f'Cache read failed: {e}')
    return None


def cache_config(config_dict: dict):
    try:
        cache.set(CONFIG_CACHE_KEY, json.dumps(config_dict), CACHE_TTL)
    except Exception as e:
        logger.debug(f'Config cache write failed: {e}')


def get_cached_config() -> dict | None:
    try:
        raw = cache.get(CONFIG_CACHE_KEY)
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.debug(f'Config cache read failed: {e}')
    return None


def invalidate_all():
    """Call after reset."""
    try:
        cache.delete_many([ECONOMY_CACHE_KEY, CONFIG_CACHE_KEY, AGENT_STATS_CACHE_KEY])
    except Exception:
        pass