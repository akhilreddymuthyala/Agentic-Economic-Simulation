from django.db import models


class PolicyState(models.Model):
    tax_rate = models.FloatField(default=20.0)
    interest_rate = models.FloatField(default=5.0)
    government_spending = models.FloatField(default=10000.0)
    subsidy_level = models.FloatField(default=0.0)
    stimulus_active = models.BooleanField(default=False)
    stimulus_amount = models.FloatField(default=0.0)
    market_regulation = models.FloatField(default=50.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'policy_state'

    def __str__(self):
        return f'PolicyState tax={self.tax_rate}% interest={self.interest_rate}%'

    @classmethod
    def get_active(cls):
        policy, _ = cls.objects.get_or_create(pk=1)
        return policy