from django.db import models


class EventType(models.TextChoices):
    RECESSION = 'recession', 'Recession'
    MARKET_CRASH = 'market_crash', 'Market Crash'
    PANIC_WAVE = 'panic_wave', 'Panic Wave'
    MONOPOLY = 'monopoly', 'Monopoly Formation'
    INNOVATION_BOOM = 'innovation_boom', 'Innovation Boom'
    UNEMPLOYMENT_CRISIS = 'unemployment_crisis', 'Unemployment Crisis'
    SHORTAGE = 'shortage', 'Resource Shortage'
    RECOVERY = 'recovery', 'Economic Recovery'


class SimulationEvent(models.Model):
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    severity = models.FloatField(default=1.0)
    description = models.TextField()
    simulation_day = models.IntegerField()
    simulation_month = models.IntegerField()
    simulation_year = models.IntegerField()
    tick_number = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'simulation_events'
        ordering = ['-tick_number']

    def __str__(self):
        return f'Event {self.event_type} tick={self.tick_number}'