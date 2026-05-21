"""
Lightweight tick profiler.
Logs slow steps so we can identify bottlenecks.
"""
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Warn if any step exceeds this threshold (seconds)
SLOW_STEP_THRESHOLD = 0.5


@contextmanager
def profile_step(step_name: str, tick: int):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        if elapsed > SLOW_STEP_THRESHOLD:
            logger.warning(
                f'[Tick {tick}] SLOW STEP: {step_name} took {elapsed:.3f}s '
                f'(threshold {SLOW_STEP_THRESHOLD}s)'
            )
        else:
            logger.debug(f'[Tick {tick}] {step_name}: {elapsed:.3f}s')


class TickProfiler:
    def __init__(self, tick: int):
        self.tick = tick
        self.steps: dict[str, float] = {}
        self._start = time.perf_counter()

    def mark(self, step: str):
        self.steps[step] = time.perf_counter() - self._start

    def report(self):
        total = time.perf_counter() - self._start
        if total > 1.0 or self.tick % 240 == 0:
            parts = ' | '.join(f'{k}:{v:.3f}s' for k, v in self.steps.items())
            logger.info(f'[Tick {self.tick}] Profile: total={total:.3f}s | {parts}')
        return total