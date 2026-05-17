from rest_framework import serializers
from .models import SimulationConfig


class SimulationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationConfig
        fields = '__all__'