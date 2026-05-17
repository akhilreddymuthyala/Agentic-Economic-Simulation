from django.contrib import admin
from .models import SimulationEvent


@admin.register(SimulationEvent)
class SimulationEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'severity', 'simulation_year', 'simulation_month', 'simulation_day']