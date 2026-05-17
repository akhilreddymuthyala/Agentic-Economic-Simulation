from django.db import models


class EconomyState(models.Model):
    gdp = models.FloatField(default=100000.0)
    inflation = models.FloatField(default=2.0)
    unemployment = models.FloatField(default=5.0)
    market_confidence = models.FloatField(default=70.0)
    wealth_gini = models.FloatField(default=0.35)
    resource_index = models.FloatField(default=100.0)
    economic_stability = models.FloatField(default=75.0)
    simulation_day = models.IntegerField(default=1)
    simulation_month = models.IntegerField(default=1)
    simulation_year = models.IntegerField(default=1)
    simulation_hour = models.IntegerField(default=0)
    tick_number = models.BigIntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'economy_state'
        ordering = ['-tick_number']

    def __str__(self):
        return f'EconomyState tick={self.tick_number}'


class Transaction(models.Model):
    buyer = models.ForeignKey(
        'agents.Agent', on_delete=models.SET_NULL,
        null=True, related_name='purchases'
    )
    seller = models.ForeignKey(
        'agents.Agent', on_delete=models.SET_NULL,
        null=True, related_name='sales'
    )
    amount = models.FloatField()
    resource = models.CharField(max_length=100)
    simulation_day = models.IntegerField()
    simulation_month = models.IntegerField()
    simulation_year = models.IntegerField()
    tick_number = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transactions'

    def __str__(self):
        return f'Transaction {self.amount} ({self.resource})'