from django.db import models


class EconomyState(models.Model):
    # Core metrics
    gdp = models.FloatField(default=100000.0)
    gdp_growth_rate = models.FloatField(default=0.0)
    inflation = models.FloatField(default=2.0)
    unemployment = models.FloatField(default=5.0)
    market_confidence = models.FloatField(default=70.0)
    wealth_gini = models.FloatField(default=0.35)
    resource_index = models.FloatField(default=100.0)
    economic_stability = models.FloatField(default=75.0)

    # Money supply
    total_money_supply = models.FloatField(default=500000.0)
    total_wealth = models.FloatField(default=500000.0)

    # Simulation time this record was taken
    tick_number = models.BigIntegerField(default=0)
    simulation_hour = models.IntegerField(default=0)
    simulation_day = models.IntegerField(default=1)
    simulation_month = models.IntegerField(default=1)
    simulation_year = models.IntegerField(default=1)

    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'economy_state'
        ordering = ['-tick_number']
        indexes = [
            models.Index(fields=['tick_number']),
            models.Index(fields=['simulation_year', 'simulation_month', 'simulation_day']),
        ]

    def __str__(self):
        return f'EconomyState tick={self.tick_number} gdp={self.gdp:.0f}'

    @classmethod
    def get_latest(cls):
        return cls.objects.order_by('-tick_number').first()

    @classmethod
    def get_initial(cls):
        """Return a dict of initial economy values for seeding."""
        return {
            'gdp': 100000.0,
            'gdp_growth_rate': 0.0,
            'inflation': 2.0,
            'unemployment': 5.0,
            'market_confidence': 70.0,
            'wealth_gini': 0.35,
            'resource_index': 100.0,
            'economic_stability': 75.0,
            'total_money_supply': 500000.0,
            'total_wealth': 500000.0,
        }


class Transaction(models.Model):
    buyer = models.ForeignKey(
        'agents.Agent', on_delete=models.SET_NULL,
        null=True, related_name='purchases',
    )
    seller = models.ForeignKey(
        'agents.Agent', on_delete=models.SET_NULL,
        null=True, related_name='sales',
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
        indexes = [
            models.Index(fields=['tick_number']),
        ]

    def __str__(self):
        return f'Transaction {self.amount} ({self.resource}) tick={self.tick_number}'