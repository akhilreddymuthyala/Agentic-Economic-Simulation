from django.contrib import admin
from .models import AgentEmotionLog


@admin.register(AgentEmotionLog)
class AgentEmotionLogAdmin(admin.ModelAdmin):
    list_display = ['agent', 'dominant_emotion', 'fear', 'panic', 'tick_number']