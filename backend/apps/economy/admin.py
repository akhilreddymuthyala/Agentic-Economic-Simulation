from django.contrib import admin
from .models import EconomyState, Transaction


@admin.register(EconomyState)
class EconomyStateAdmin(admin.ModelAdmin):
    list_display = ['tick_number', 'gdp', 'inflation', 'unemployment', 'market_confidence']
    ordering = ['-tick_number']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'buyer', 'seller', 'amount', 'resource', 'tick_number']