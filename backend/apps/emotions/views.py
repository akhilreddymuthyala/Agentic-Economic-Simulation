from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Avg, Count
from apps.agents.models import Agent
from apps.emotions.models import AgentEmotionLog
from apps.emotions.behavior_mapper import get_behavior_modifiers


class EmotionDistributionView(APIView):
    def get(self, request):
        dist = (
            Agent.objects
            .filter(is_active=True)
            .values('dominant_emotion')
            .annotate(count=Count('id'), avg_fear=Avg('emotion_fear'),
                      avg_panic=Avg('emotion_panic'))
            .order_by('dominant_emotion')
        )
        society = Agent.objects.filter(is_active=True).aggregate(
            avg_fear=Avg('emotion_fear'),
            avg_greed=Avg('emotion_greed'),
            avg_trust=Avg('emotion_trust'),
            avg_optimism=Avg('emotion_optimism'),
            avg_stress=Avg('emotion_stress'),
            avg_panic=Avg('emotion_panic'),
        )
        return Response({
            'distribution': list(dist),
            'society_averages': society,
        })


class AgentEmotionHistoryView(APIView):
    def get(self, request, agent_id):
        limit = int(request.query_params.get('limit', 48))
        logs = AgentEmotionLog.objects.filter(
            agent_id=agent_id
        ).order_by('-tick_number')[:limit]

        data = [
            {
                'tick': log.tick_number,
                'fear': log.fear,
                'greed': log.greed,
                'trust': log.trust,
                'optimism': log.optimism,
                'stress': log.stress,
                'panic': log.panic,
                'dominant': log.dominant_emotion,
            }
            for log in logs
        ]
        return Response(data)