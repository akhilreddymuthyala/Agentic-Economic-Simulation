from rest_framework import serializers
from .models import PolicyState


class PolicyStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyState
        fields = '__all__'