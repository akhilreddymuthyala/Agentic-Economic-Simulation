from django.contrib import admin
from .models import AgentMemory


@admin.register(AgentMemory)
class AgentMemoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'agent', 'memory_type', 'importance', 'tick_number', 'created_at']
    list_filter = ['memory_type']
    search_fields = ['agent__name', 'memory_text']
    readonly_fields = ['created_at']