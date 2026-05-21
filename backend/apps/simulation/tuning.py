"""
Central tuning parameters for emergent behavior.
Adjust these to make recessions, crashes, and recoveries emerge naturally.
"""

# ── Economy ────────────────────────────────────────────────────────────────

# GDP: how strongly transaction volume feeds into GDP
GDP_TRANSACTION_MULTIPLIER = 8.0

# Inflation: money supply sensitivity
INFLATION_MONEY_SENSITIVITY = 40.0

# Market confidence: emotion sensitivity
CONFIDENCE_EMOTION_SENSITIVITY = 15.0

# Economic stability composite weights
STABILITY_INFLATION_WEIGHT = 1.5
STABILITY_UNEMPLOYMENT_WEIGHT = 1.2
STABILITY_INEQUALITY_WEIGHT = 25.0

# ── Emotions ───────────────────────────────────────────────────────────────

# How quickly emotions decay toward baseline per tick
EMOTION_DECAY_RATES = {
    'fear':     0.010,
    'greed':    0.008,
    'trust':    0.004,
    'optimism': 0.006,
    'stress':   0.012,
    'panic':    0.018,
}

# Baseline values emotions revert toward
EMOTION_BASELINES = {
    'fear':     0.08,
    'greed':    0.18,
    'trust':    0.45,
    'optimism': 0.35,
    'stress':   0.12,
    'panic':    0.03,
}

# Economy trigger delta magnitudes
TRIGGER_SCALE = 1.0  # multiply all deltas by this — increase for more volatile emotions

# ── Social Influence ──────────────────────────────────────────────────────

# How strongly emotions spread through social graph
SOCIAL_INFLUENCE_SCALE = 0.06

# Herd threshold — what fraction of neighbors sharing emotion triggers herd
HERD_THRESHOLD = 0.45

# Panic wave threshold
PANIC_WAVE_THRESHOLD = 0.35
PANIC_WAVE_BOOST = 0.12

# ── Event Detection ───────────────────────────────────────────────────────

# Recession: GDP must decline this many consecutive days
RECESSION_DAYS = 3
RECESSION_PCT = -0.3

# Market crash: confidence must drop this much in one day
CRASH_DROP = 12.0
CRASH_THRESHOLD = 38.0

# Panic wave: this fraction of agents must be fearful/panic
PANIC_AGENT_FRACTION = 0.35

# Unemployment crisis threshold
UNEMPLOYMENT_CRISIS_PCT = 20.0

# Innovation boom: GDP growth and researcher wealth thresholds
INNOVATION_GDP_GROWTH = 0.3
INNOVATION_RESEARCHER_WEALTH = 6000.0

# ── Circulation ───────────────────────────────────────────────────────────

# How often full circulation runs (every N ticks)
CIRCULATION_INTERVAL = 4

# Wage rate: business owners pay workers this fraction of their wealth per interval
WAGE_RATE = 0.03

# Consumer spend rate
CONSUMER_SPEND_RATE = 0.025

# Tax collection rate per tick (on top of policy tax rate)
TAX_COLLECTION_RATE = 0.0015