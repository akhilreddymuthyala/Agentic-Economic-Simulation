from rest_framework import serializers
from .models import ResourceState


class ResourceStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceState
        fields = '__all__'