from django.contrib import admin
from .models import SimulationConfig


@admin.register(SimulationConfig)
class SimulationConfigAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'status', 'speed_multiplier', 'current_tick',
        'current_year', 'current_month', 'current_day', 'current_hour',
    ]
    readonly_fields = ['created_at', 'updated_at']