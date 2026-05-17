from django.db import models


class AgentRole(models.TextChoices):
    CONSUMER = 'consumer', 'Consumer'
    WORKER = 'worker', 'Worker'
    TRADER = 'trader', 'Trader'
    INVESTOR = 'investor', 'Investor'
    BUSINESS_OWNER = 'business_owner', 'Business Owner'
    MANUFACTURER = 'manufacturer', 'Manufacturer'
    GOVERNMENT = 'government', 'Government Agent'
    BANKER = 'banker', 'Banker'
    INFLUENCER = 'influencer', 'Influencer'
    RESEARCHER = 'researcher', 'Researcher'
    RESOURCE_SUPPLIER = 'resource_supplier', 'Resource Supplier'


class AgentStrategy(models.TextChoices):
    CONSERVATIVE = 'conservative', 'Conservative'
    AGGRESSIVE = 'aggressive', 'Aggressive'
    BALANCED = 'balanced', 'Balanced'
    SPECULATIVE = 'speculative', 'Speculative'
    COOPERATIVE = 'cooperative', 'Cooperative'


class AgentEmotionState(models.TextChoices):
    NEUTRAL = 'neutral', 'Neutral'
    FEARFUL = 'fearful', 'Fearful'
    GREEDY = 'greedy', 'Greedy'
    TRUSTING = 'trusting', 'Trusting'
    OPTIMISTIC = 'optimistic', 'Optimistic'
    STRESSED = 'stressed', 'Stressed'
    PANIC = 'panic', 'Panic'


class Agent(models.Model):
    # Identity
    name = models.CharField(max_length=100)
    profession = models.CharField(max_length=50, choices=AgentRole.choices)
    intelligence_tier = models.IntegerField(default=3)  # 1=LLM, 2=Neural, 3=Rule

    # Economic state
    wealth = models.FloatField(default=1000.0)
    income = models.FloatField(default=0.0)
    debt = models.FloatField(default=0.0)

    # Emotion state — stored as individual floats
    emotion_fear = models.FloatField(default=0.0)
    emotion_greed = models.FloatField(default=0.0)
    emotion_trust = models.FloatField(default=0.5)
    emotion_optimism = models.FloatField(default=0.5)
    emotion_stress = models.FloatField(default=0.0)
    emotion_panic = models.FloatField(default=0.0)
    dominant_emotion = models.CharField(
        max_length=20,
        choices=AgentEmotionState.choices,
        default=AgentEmotionState.NEUTRAL,
    )

    # Decision attributes
    risk_score = models.FloatField(default=0.5)
    strategy = models.CharField(
        max_length=50,
        choices=AgentStrategy.choices,
        default=AgentStrategy.BALANCED,
    )

    # Social
    social_influence = models.FloatField(default=0.5)
    cooperation_rate = models.FloatField(default=0.5)

    # Status
    is_employed = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    last_action = models.CharField(max_length=100, default='idle')
    last_action_tick = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agents'

    def __str__(self):
        return f'{self.name} ({self.profession})'

    def get_emotion_vector(self):
        return {
            'fear': self.emotion_fear,
            'greed': self.emotion_greed,
            'trust': self.emotion_trust,
            'optimism': self.emotion_optimism,
            'stress': self.emotion_stress,
            'panic': self.emotion_panic,
        }

    def compute_dominant_emotion(self):
        emotions = self.get_emotion_vector()
        # neutral baseline — if all below threshold return neutral
        if all(v < 0.3 for v in emotions.values()):
            return AgentEmotionState.NEUTRAL
        dominant = max(emotions, key=emotions.get)
        mapping = {
            'fear': AgentEmotionState.FEARFUL,
            'greed': AgentEmotionState.GREEDY,
            'trust': AgentEmotionState.TRUSTING,
            'optimism': AgentEmotionState.OPTIMISTIC,
            'stress': AgentEmotionState.STRESSED,
            'panic': AgentEmotionState.PANIC,
        }
        return mapping.get(dominant, AgentEmotionState.NEUTRAL)