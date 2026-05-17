from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db.models import Avg, Sum, Count

from .models import Agent, AgentRole
from .serializers import (
    AgentListSerializer,
    AgentDetailSerializer,
    AgentMemorySerializer,
    SocialRelationshipSerializer,
)
from apps.memory.models import AgentMemory
from apps.social.models import SocialRelationship
from apps.memory.services import retrieve_similar_memories, retrieve_memories_by_importance


class AgentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Agent.objects.filter(is_active=True).order_by('id')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AgentDetailSerializer
        return AgentListSerializer

    @action(detail=False, methods=['get'])
    def summary(self, request):
        data = (
            Agent.objects
            .values('profession')
            .annotate(
                count=Count('id'),
                avg_wealth=Avg('wealth'),
                avg_risk=Avg('risk_score'),
            )
            .order_by('profession')
        )
        totals = Agent.objects.aggregate(
            total=Count('id'),
            total_wealth=Sum('wealth'),
            avg_wealth=Avg('wealth'),
        )
        return Response({
            'by_profession': list(data),
            'totals': totals,
        })

    @action(detail=False, methods=['get'], url_path='by-role/(?P<role>[^/.]+)')
    def by_role(self, request, role=None):
        agents = self.queryset.filter(profession=role)
        serializer = AgentListSerializer(agents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def memories(self, request, pk=None):
        agent = self.get_object()
        query = request.query_params.get('query', None)
        top_k = int(request.query_params.get('top_k', 10))

        if query:
            memories = retrieve_similar_memories(agent.id, query, top_k=top_k)
        else:
            memories = retrieve_memories_by_importance(agent.id, top_k=top_k)

        serializer = AgentMemorySerializer(memories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def relationships(self, request, pk=None):
        agent = self.get_object()
        rels_a = SocialRelationship.objects.filter(agent_a=agent).select_related('agent_a', 'agent_b')
        rels_b = SocialRelationship.objects.filter(agent_b=agent).select_related('agent_a', 'agent_b')
        all_rels = list(rels_a) + list(rels_b)
        serializer = SocialRelationshipSerializer(all_rels, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def emotion_distribution(self, request):
        data = (
            Agent.objects
            .values('dominant_emotion')
            .annotate(count=Count('id'))
            .order_by('dominant_emotion')
        )
        return Response(list(data))


class AgentSocietyView(APIView):
    """Aggregate stats across all agents — for the Inspector Society view."""

    def get(self, request):
        agents = Agent.objects.filter(is_active=True)
        total = agents.count()
        employed = agents.filter(is_employed=True).count()

        stats = agents.aggregate(
            avg_wealth=Avg('wealth'),
            total_wealth=Sum('wealth'),
            avg_fear=Avg('emotion_fear'),
            avg_greed=Avg('emotion_greed'),
            avg_trust=Avg('emotion_trust'),
            avg_optimism=Avg('emotion_optimism'),
            avg_stress=Avg('emotion_stress'),
            avg_panic=Avg('emotion_panic'),
        )

        emotion_dist = list(
            agents.values('dominant_emotion')
            .annotate(count=Count('id'))
            .order_by('dominant_emotion')
        )

        profession_dist = list(
            agents.values('profession')
            .annotate(count=Count('id'), avg_wealth=Avg('wealth'))
            .order_by('profession')
        )

        return Response({
            'total_agents': total,
            'employed': employed,
            'unemployment_rate': round((1 - employed / total) * 100, 2) if total else 0,
            'aggregate_emotions': stats,
            'emotion_distribution': emotion_dist,
            'profession_distribution': profession_dist,
        })