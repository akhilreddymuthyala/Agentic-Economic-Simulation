from rest_framework import serializers
from .models import EconomyState, Transaction


class EconomyStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EconomyState
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'