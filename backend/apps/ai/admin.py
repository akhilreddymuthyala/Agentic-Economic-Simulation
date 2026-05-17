from django.contrib import admin
from .models import NeuralLog


@admin.register(NeuralLog)
class NeuralLogAdmin(admin.ModelAdmin):
    list_display = ['agent', 'decision_output', 'confidence', 'tick_number']