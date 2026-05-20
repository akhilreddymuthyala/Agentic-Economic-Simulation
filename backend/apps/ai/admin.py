from django.contrib import admin
from .models import NeuralLog


@admin.register(NeuralLog)
class NeuralLogAdmin(admin.ModelAdmin):
    list_display = ['agent', 'decision_output', 'confidence', 'reasoning', 'tick_number']
    list_filter = ['decision_output']
    search_fields = ['agent__name', 'reasoning']