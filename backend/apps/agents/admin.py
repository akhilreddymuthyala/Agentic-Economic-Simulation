from django.contrib import admin
from .models import Agent


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'profession', 'wealth', 'dominant_emotion',
        'risk_score', 'strategy', 'intelligence_tier', 'is_employed', 'is_active',
    ]
    list_filter = ['profession', 'intelligence_tier', 'dominant_emotion', 'strategy', 'is_active']
    search_fields = ['name', 'profession']
    readonly_fields = ['created_at', 'updated_at']