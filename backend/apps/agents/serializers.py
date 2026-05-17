from rest_framework import serializers
from .models import Agent
from apps.memory.models import AgentMemory
from apps.social.models import SocialRelationship


class AgentEmotionSerializer(serializers.Serializer):
    fear = serializers.FloatField(source='emotion_fear')
    greed = serializers.FloatField(source='emotion_greed')
    trust = serializers.FloatField(source='emotion_trust')
    optimism = serializers.FloatField(source='emotion_optimism')
    stress = serializers.FloatField(source='emotion_stress')
    panic = serializers.FloatField(source='emotion_panic')


class AgentListSerializer(serializers.ModelSerializer):
    emotion_vector = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = [
            'id', 'name', 'profession', 'wealth', 'dominant_emotion',
            'emotion_vector', 'risk_score', 'strategy', 'intelligence_tier',
            'is_employed', 'is_active', 'last_action', 'social_influence',
        ]

    def get_emotion_vector(self, obj):
        return obj.get_emotion_vector()


class AgentDetailSerializer(serializers.ModelSerializer):
    emotion_vector = serializers.SerializerMethodField()
    memory_count = serializers.SerializerMethodField()
    relationship_count = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = '__all__'

    def get_emotion_vector(self, obj):
        return obj.get_emotion_vector()

    def get_memory_count(self, obj):
        return obj.memories.count()

    def get_relationship_count(self, obj):
        return (
            obj.relationships_as_a.count() +
            obj.relationships_as_b.count()
        )


class AgentMemorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentMemory
        fields = [
            'id', 'memory_text', 'importance', 'memory_type',
            'tick_number', 'simulation_day', 'simulation_year', 'created_at',
        ]


class SocialRelationshipSerializer(serializers.ModelSerializer):
    agent_a_name = serializers.CharField(source='agent_a.name', read_only=True)
    agent_b_name = serializers.CharField(source='agent_b.name', read_only=True)
    agent_a_profession = serializers.CharField(source='agent_a.profession', read_only=True)
    agent_b_profession = serializers.CharField(source='agent_b.profession', read_only=True)

    class Meta:
        model = SocialRelationship
        fields = [
            'id', 'agent_a', 'agent_a_name', 'agent_a_profession',
            'agent_b', 'agent_b_name', 'agent_b_profession',
            'trust_score', 'influence_score', 'relationship_type',
            'interaction_count',
        ]