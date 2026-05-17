from django.contrib import admin
from .models import SimulationSnapshot


@admin.register(SimulationSnapshot)
class SimulationSnapshotAdmin(admin.ModelAdmin):
    list_display = ['id', 'label', 'tick_number', 'simulation_year',
                    'simulation_month', 'simulation_day', 'created_at']
    readonly_fields = ['created_at']