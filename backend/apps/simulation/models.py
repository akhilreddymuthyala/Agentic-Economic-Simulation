from django.db import models


class SimulationStatus(models.TextChoices):
    IDLE = 'idle', 'Idle'
    RUNNING = 'running', 'Running'
    PAUSED = 'paused', 'Paused'
    STOPPED = 'stopped', 'Stopped'


class SimulationConfig(models.Model):
    status = models.CharField(
        max_length=20,
        choices=SimulationStatus.choices,
        default=SimulationStatus.IDLE,
    )
    speed_multiplier = models.IntegerField(default=1)
    current_tick = models.BigIntegerField(default=0)
    current_day = models.IntegerField(default=1)
    current_month = models.IntegerField(default=1)
    current_year = models.IntegerField(default=1)
    current_hour = models.IntegerField(default=0)
    total_agents = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'simulation_config'

    def __str__(self):
        return f'SimulationConfig status={self.status} speed={self.speed_multiplier}x'

    @classmethod
    def get_active(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config