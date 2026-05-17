from django.contrib import admin
from .models import PolicyState


@admin.register(PolicyState)
class PolicyStateAdmin(admin.ModelAdmin):
    list_display = ['id', 'tax_rate', 'interest_rate', 'government_spending', 'stimulus_active']