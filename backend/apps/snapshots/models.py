from django.db import models


class SimulationSnapshot(models.Model):
    label = models.CharField(max_length=200, blank=True, default='')
    tick_number = models.BigIntegerField()
    simulation_day = models.IntegerField()
    simulation_month = models.IntegerField()
    simulation_year = models.IntegerField()
    state_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'simulation_snapshots'
        ordering = ['-tick_number']

    def __str__(self):
        return f'Snapshot id={self.pk} tick={self.tick_number} — {self.label}'