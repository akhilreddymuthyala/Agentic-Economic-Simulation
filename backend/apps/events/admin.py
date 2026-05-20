from django.contrib import admin
from .models import SimulationEvent


@admin.register(SimulationEvent)
class SimulationEventAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'event_type', 'severity',
        'simulation_year', 'simulation_month', 'simulation_day',
        'tick_number', 'created_at',
    ]
    list_filter = ['event_type']
    search_fields = ['description']
    ordering = ['-tick_number']