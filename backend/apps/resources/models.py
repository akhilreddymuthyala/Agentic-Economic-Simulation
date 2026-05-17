from django.db import models


class ResourceState(models.Model):
    food_supply = models.FloatField(default=100.0)
    oil_supply = models.FloatField(default=100.0)
    energy_availability = models.FloatField(default=100.0)
    housing_supply = models.FloatField(default=100.0)
    water_resources = models.FloatField(default=100.0)
    food_price = models.FloatField(default=10.0)
    oil_price = models.FloatField(default=50.0)
    energy_price = models.FloatField(default=30.0)
    housing_price = models.FloatField(default=200.0)
    water_price = models.FloatField(default=5.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'resource_state'

    def __str__(self):
        return f'ResourceState food={self.food_supply} oil={self.oil_supply}'

    @classmethod
    def get_active(cls):
        resource, _ = cls.objects.get_or_create(pk=1)
        return resource