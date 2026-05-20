"""
Event Detection Engine — Phase 7

Detects emergent economic events each tick:
- Recession
- Market Crash
- Panic Wave
- Monopoly Formation
- Innovation Boom
- Unemployment Crisis
- Shortage Event
- Economic Recovery
"""
import logging
from collections import deque
from django.db.models import Sum, Count, Q
from apps.events.models import SimulationEvent, EventType
from apps.agents.models import Agent, AgentRole

logger = logging.getLogger(__name__)

# ── Detection thresholds ──────────────────────────────────────────────────────
RECESSION_GDP_DECLINE_DAYS = 3          # consecutive days of GDP decline
RECESSION_GDP_DECLINE_PCT = -0.5        # % decline per day to count

MARKET_CRASH_CONFIDENCE_THRESHOLD = 35.0
MARKET_CRASH_CONFIDENCE_DROP = 15.0    # drop within 24 ticks

PANIC_WAVE_AGENT_PCT = 0.40             # 40% of agents in panic/fear

MONOPOLY_WEALTH_PCT = 0.50             # 50% of business owner wealth

INNOVATION_BOOM_RESEARCHER_THRESHOLD = 2  # researchers needed
INNOVATION_BOOM_WEALTH_GROWTH = 0.05      # 5% wealth growth in researcher group

UNEMPLOYMENT_CRISIS_THRESHOLD = 25.0

SHORTAGE_CRITICAL_LEVEL = 20.0

RECOVERY_GDP_GROWTH_THRESHOLD = 1.0    # % growth after recession

# ── Rolling history for trend detection ───────────────────────────────────────
# Stores last 72 economy snapshots (3 sim days at 24 ticks/day)
_gdp_history = deque(maxlen=72)
_confidence_history = deque(maxlen=48)
_recession_active = False
_last_event_ticks = {}   # event_type → last tick it fired (cooldown)
EVENT_COOLDOWN_TICKS = 48  # don't re-fire same event within 48 ticks


def _on_cooldown(event_type: str, tick: int) -> bool:
    last = _last_event_ticks.get(event_type, -9999)
    return (tick - last) < EVENT_COOLDOWN_TICKS


def _record_event(event_type: str, severity: float, description: str,
                  context: dict, affected_agent_ids: list = None) -> SimulationEvent:
    """Persist event to DB and add to context for broadcasting."""
    global _last_event_ticks
    tick = context['tick']
    _last_event_ticks[event_type] = tick

    event = SimulationEvent.objects.create(
        event_type=event_type,
        severity=severity,
        description=description,
        simulation_day=context['day'],
        simulation_month=context['month'],
        simulation_year=context['year'],
        tick_number=tick,
    )

    event_payload = {
        'type': 'simulation_event',
        'event_type': event_type,
        'severity': severity,
        'description': description,
        'year': context['year'],
        'month': context['month'],
        'day': context['day'],
        'hour': context['hour'],
        'tick': tick,
    }

    context['events_detected'].append(event_payload)

    logger.warning(
        f'[EVENT][Tick {tick}] {event_type.upper()} — {description}'
    )
    return event


# ── Individual detectors ──────────────────────────────────────────────────────

def detect_recession(context: dict) -> dict:
    global _recession_active
    tick = context['tick']
    gdp = context['economy']['gdp']
    _gdp_history.append((tick, gdp))

    if len(_gdp_history) < RECESSION_GDP_DECLINE_DAYS * 24:
        return context

    # Check last 3 sim days (72 ticks) — compare daily snapshots
    daily_gdps = []
    for i in range(0, min(len(_gdp_history), 72), 24):
        idx = -(i + 1)
        try:
            daily_gdps.append(_gdp_history[idx][1])
        except IndexError:
            break

    if len(daily_gdps) < 3:
        return context

    # Count consecutive days of decline
    declining_days = 0
    for i in range(len(daily_gdps) - 1):
        if daily_gdps[i] > 0:
            pct_change = (daily_gdps[i + 1] - daily_gdps[i]) / daily_gdps[i] * 100
            if pct_change < RECESSION_GDP_DECLINE_PCT:
                declining_days += 1

    if declining_days >= RECESSION_GDP_DECLINE_DAYS and not _recession_active:
        if not _on_cooldown(EventType.RECESSION, tick):
            _recession_active = True
            severity = min(1.0, declining_days / 10.0)
            _record_event(
                EventType.RECESSION, severity,
                f'Recession detected — GDP has declined for {declining_days} consecutive days. '
                f'Current GDP: {gdp:.0f}',
                context,
            )
    elif declining_days == 0 and _recession_active:
        _recession_active = False

    return context


def detect_market_crash(context: dict) -> dict:
    tick = context['tick']
    confidence = context['economy']['market_confidence']
    _confidence_history.append((tick, confidence))

    if confidence < MARKET_CRASH_CONFIDENCE_THRESHOLD:
        if not _on_cooldown(EventType.MARKET_CRASH, tick):
            # Check how fast it dropped
            if len(_confidence_history) >= 24:
                old_confidence = _confidence_history[-24][1]
                drop = old_confidence - confidence
                if drop >= MARKET_CRASH_CONFIDENCE_DROP:
                    severity = min(1.0, drop / 50.0)
                    _record_event(
                        EventType.MARKET_CRASH, severity,
                        f'Market crash — confidence collapsed from {old_confidence:.1f}% '
                        f'to {confidence:.1f}% in one simulation day.',
                        context,
                    )
    return context


def detect_panic_wave(context: dict) -> dict:
    tick = context['tick']
    if _on_cooldown(EventType.PANIC_WAVE, tick):
        return context

    total = Agent.objects.filter(is_active=True).count()
    if total == 0:
        return context

    panic_fear_count = Agent.objects.filter(
        is_active=True,
        dominant_emotion__in=['panic', 'fearful'],
    ).count()

    ratio = panic_fear_count / total
    if ratio >= PANIC_WAVE_AGENT_PCT:
        severity = min(1.0, ratio)
        _record_event(
            EventType.PANIC_WAVE, severity,
            f'Panic wave spreading — {panic_fear_count} of {total} agents '
            f'({ratio * 100:.0f}%) are in fear or panic.',
            context,
        )
    return context


def detect_monopoly(context: dict) -> dict:
    tick = context['tick']
    if _on_cooldown(EventType.MONOPOLY, tick):
        return context

    business_agents = Agent.objects.filter(
        profession=AgentRole.BUSINESS_OWNER,
        is_active=True,
    )
    total_business_wealth = business_agents.aggregate(
        total=Sum('wealth')
    )['total'] or 0

    if total_business_wealth == 0:
        return context

    for agent in business_agents:
        share = agent.wealth / total_business_wealth
        if share >= MONOPOLY_WEALTH_PCT:
            severity = min(1.0, share)
            _record_event(
                EventType.MONOPOLY, severity,
                f'Monopoly forming — {agent.name} controls '
                f'{share * 100:.0f}% of business wealth (${agent.wealth:.0f}).',
                context,
                affected_agent_ids=[agent.id],
            )
            break

    return context


def detect_innovation_boom(context: dict) -> dict:
    tick = context['tick']
    if _on_cooldown(EventType.INNOVATION_BOOM, tick):
        return context

    researchers = list(Agent.objects.filter(
        profession=AgentRole.RESEARCHER,
        is_active=True,
    ))

    if len(researchers) < INNOVATION_BOOM_RESEARCHER_THRESHOLD:
        return context

    # Check if researchers are accumulating wealth (proxy for innovation success)
    avg_researcher_wealth = sum(r.wealth for r in researchers) / len(researchers)
    gdp_growth = context['economy'].get('gdp_growth_rate', 0)
    market_conf = context['economy'].get('market_confidence', 70)

    if (avg_researcher_wealth > 8000 and
            gdp_growth > 0.5 and
            market_conf > 65):
        severity = min(1.0, gdp_growth / 5.0)
        _record_event(
            EventType.INNOVATION_BOOM, severity,
            f'Innovation boom — researcher productivity surge detected. '
            f'GDP growth at {gdp_growth:.2f}%, avg researcher wealth ${avg_researcher_wealth:.0f}.',
            context,
        )
    return context


def detect_unemployment_crisis(context: dict) -> dict:
    tick = context['tick']
    if _on_cooldown(EventType.UNEMPLOYMENT_CRISIS, tick):
        return context

    unemployment = context['economy']['unemployment']
    if unemployment >= UNEMPLOYMENT_CRISIS_THRESHOLD:
        severity = min(1.0, unemployment / 100.0)
        _record_event(
            EventType.UNEMPLOYMENT_CRISIS, severity,
            f'Unemployment crisis — {unemployment:.1f}% of workforce jobless. '
            f'Mass layoffs destabilising the economy.',
            context,
        )
    return context


def detect_shortage_events(context: dict) -> dict:
    tick = context['tick']
    shortages = context.get('resource_shortages', [])

    for shortage in shortages:
        resource = shortage['resource']
        supply = shortage['supply']
        event_key = f'shortage_{resource}'

        if _on_cooldown(event_key, tick):
            continue

        _last_event_ticks[event_key] = tick
        severity = max(0.1, (SHORTAGE_CRITICAL_LEVEL - supply) / SHORTAGE_CRITICAL_LEVEL)

        SimulationEvent.objects.create(
            event_type=EventType.SHORTAGE,
            severity=severity,
            description=f'{resource.capitalize()} shortage critical — '
                        f'supply at {supply:.1f}%. Prices spiking, panic spreading.',
            simulation_day=context['day'],
            simulation_month=context['month'],
            simulation_year=context['year'],
            tick_number=tick,
        )

        context['events_detected'].append({
            'type': 'simulation_event',
            'event_type': EventType.SHORTAGE,
            'severity': severity,
            'description': f'{resource.capitalize()} shortage critical — supply at {supply:.1f}%.',
            'year': context['year'],
            'month': context['month'],
            'day': context['day'],
            'hour': context['hour'],
            'tick': tick,
        })

    return context


def detect_economic_recovery(context: dict) -> dict:
    global _recession_active
    tick = context['tick']

    if not _recession_active:
        return context
    if _on_cooldown(EventType.RECOVERY, tick):
        return context

    gdp_growth = context['economy'].get('gdp_growth_rate', 0)
    if gdp_growth >= RECOVERY_GDP_GROWTH_THRESHOLD:
        _recession_active = False
        severity = min(1.0, gdp_growth / 5.0)
        _record_event(
            EventType.RECOVERY, severity,
            f'Economic recovery underway — GDP growing at {gdp_growth:.2f}%. '
            f'Market confidence rebuilding after recession.',
            context,
        )
    return context


# ── Main entry point ──────────────────────────────────────────────────────────

DETECTORS = [
    detect_recession,
    detect_market_crash,
    detect_panic_wave,
    detect_monopoly,
    detect_innovation_boom,
    detect_unemployment_crisis,
    detect_shortage_events,
    detect_economic_recovery,
]


def run_event_detection(context: dict) -> dict:
    """
    Run all event detectors each tick.
    Detectors are cheap — most return instantly if conditions aren't met.
    Heavy DB queries only fire when thresholds are approached.
    """
    tick = context['tick']

    # Initialise events list if not present
    if 'events_detected' not in context:
        context['events_detected'] = []

    # Run all detectors
    for detector in DETECTORS:
        try:
            context = detector(context)
        except Exception as e:
            logger.error(f'[Tick {tick}] Detector {detector.__name__} failed: {e}')

    if context['events_detected'] and tick % 24 == 0:
        logger.info(
            f'[Tick {tick}] {len(context["events_detected"])} events detected this tick.'
        )

    return context