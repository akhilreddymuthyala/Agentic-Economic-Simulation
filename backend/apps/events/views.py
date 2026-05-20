from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from .models import SimulationEvent


class SimulationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationEvent
        fields = [
            'id', 'event_type', 'severity', 'description',
            'simulation_year', 'simulation_month', 'simulation_day',
            'tick_number', 'created_at',
        ]


class EventListView(APIView):
    def get(self, request):
        event_type = request.query_params.get('type')
        limit = int(request.query_params.get('limit', 50))

        qs = SimulationEvent.objects.order_by('-tick_number')
        if event_type:
            qs = qs.filter(event_type=event_type)

        return Response(SimulationEventSerializer(qs[:limit], many=True).data)


class EventSummaryView(APIView):
    def get(self, request):
        from django.db.models import Count, Avg, Max
        summary = (
            SimulationEvent.objects
            .values('event_type')
            .annotate(
                count=Count('id'),
                avg_severity=Avg('severity'),
                last_tick=Max('tick_number'),
            )
            .order_by('-count')
        )
        return Response(list(summary))