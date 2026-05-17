from django.contrib import admin
from .models import ResourceState


@admin.register(ResourceState)
class ResourceStateAdmin(admin.ModelAdmin):
    list_display = ['id', 'food_supply', 'oil_supply', 'energy_availability', 'housing_supply']