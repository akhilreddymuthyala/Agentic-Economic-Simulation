"""
Step 5: Detect Events — now calls the real event detection engine.
"""
import logging
from apps.events.engine import run_event_detection

logger = logging.getLogger(__name__)


def detect_events(context: dict) -> dict:
    context = run_event_detection(context)
    return context