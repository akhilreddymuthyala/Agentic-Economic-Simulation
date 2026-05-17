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
    current_hour = models.IntegerField(default=0)
    current_day = models.IntegerField(default=1)
    current_week = models.IntegerField(default=1)
    current_month = models.IntegerField(default=1)
    current_year = models.IntegerField(default=1)
    total_agents = models.IntegerField(default=100)
    # Celery task id for the running tick scheduler
    celery_task_id = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'simulation_config'

    def __str__(self):
        return (
            f'SimulationConfig status={self.status} '
            f'speed={self.speed_multiplier}x tick={self.current_tick}'
        )

    @classmethod
    def get_active(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def advance_tick(self):
        """Advance clock by one tick and update all calendar fields."""
        from apps.simulation.clock import tick_to_datetime
        self.current_tick += 1
        dt = tick_to_datetime(self.current_tick)
        self.current_hour = dt['hour']
        self.current_day = dt['day']
        self.current_week = dt['week']
        self.current_month = dt['month']
        self.current_year = dt['year']

    def reset_clock(self):
        self.current_tick = 0
        self.current_hour = 0
        self.current_day = 1
        self.current_week = 1
        self.current_month = 1
        self.current_year = 1