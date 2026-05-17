from rest_framework import serializers
from .models import SimulationConfig


class SimulationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationConfig
        fields = [
            'id', 'status', 'speed_multiplier',
            'current_tick', 'current_hour', 'current_day',
            'current_week', 'current_month', 'current_year',
            'total_agents', 'celery_task_id',
            'created_at', 'updated_at',
        ]