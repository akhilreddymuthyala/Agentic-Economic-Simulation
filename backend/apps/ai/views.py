from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg
from apps.ai.models import NeuralLog
from apps.agents.models import Agent


class NeuralLogListView(APIView):
    def get(self, request):
        agent_id = request.query_params.get('agent_id')
        limit = int(request.query_params.get('limit', 20))

        qs = NeuralLog.objects.order_by('-tick_number')
        if agent_id:
            qs = qs.filter(agent_id=agent_id)

        logs = qs[:limit].values(
            'agent_id', 'agent__name', 'agent__profession',
            'decision_output', 'confidence', 'reasoning', 'tick_number',
        )
        return Response(list(logs))


class DecisionSummaryView(APIView):
    def get(self, request):
        from apps.agents.models import Agent
        from django.db.models import Count

        actions = (
            Agent.objects.filter(is_active=True)
            .values('last_action')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        tiers = (
            Agent.objects.filter(is_active=True)
            .values('intelligence_tier')
            .annotate(count=Count('id'), avg_wealth=Avg('wealth'))
            .order_by('intelligence_tier')
        )
        return Response({
            'action_distribution': list(actions),
            'tier_distribution': list(tiers),
        })