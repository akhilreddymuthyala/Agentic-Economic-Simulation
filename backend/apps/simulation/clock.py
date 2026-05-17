"""
Virtual calendar system for the simulation.

Time mapping:
    1 tick          = 1 simulation hour
    24 ticks        = 1 simulation day
    30 days         = 1 simulation month
    12 months       = 1 simulation year

Real-world interval per tick at each speed:
    1x  → 5 min/day  → 300s/day  → 12.5s per tick
    5x  → 1 min/day  → 60s/day   → 2.5s per tick
    10x → 30s/day    → 30s/day   → 1.25s per tick
    25x → 12s/day    → 12s/day   → 0.5s per tick
    50x → 6s/day     → 6s/day    → 0.25s per tick
"""

TICKS_PER_HOUR = 1
TICKS_PER_DAY = 24
DAYS_PER_MONTH = 30
MONTHS_PER_YEAR = 12
TICKS_PER_MONTH = TICKS_PER_DAY * DAYS_PER_MONTH        # 720
TICKS_PER_YEAR = TICKS_PER_MONTH * MONTHS_PER_YEAR      # 8640

# Real seconds for one full simulation day at each speed multiplier
SECONDS_PER_DAY_AT_SPEED = {
    1:  300.0,   # 5 minutes
    5:  60.0,    # 1 minute
    10: 30.0,    # 30 seconds
    25: 12.0,    # 12 seconds
    50: 6.0,     # 6 seconds
}


def tick_interval_seconds(speed: int) -> float:
    """Return the real-world interval in seconds between ticks at given speed."""
    seconds_per_day = SECONDS_PER_DAY_AT_SPEED.get(speed, 300.0)
    return round(seconds_per_day / TICKS_PER_DAY, 4)


def tick_to_datetime(tick: int) -> dict:
    """Convert an absolute tick number to simulation calendar components."""
    total_hours = tick
    hour = total_hours % 24
    total_days = total_hours // 24
    day = (total_days % DAYS_PER_MONTH) + 1
    total_months = total_days // DAYS_PER_MONTH
    month = (total_months % MONTHS_PER_YEAR) + 1
    year = (total_months // MONTHS_PER_YEAR) + 1
    week = ((day - 1) // 7) + 1
    return {
        'year': year,
        'month': month,
        'week': week,
        'day': day,
        'hour': hour,
        'tick': tick,
    }


def format_sim_date(tick: int) -> str:
    dt = tick_to_datetime(tick)
    return (
        f"Year {dt['year']} — Month {dt['month']} — "
        f"Day {dt['day']} — {dt['hour']:02d}:00"
    )