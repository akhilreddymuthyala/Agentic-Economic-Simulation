from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import EconomyState, Transaction
from .serializers import EconomyStateSerializer, TransactionSerializer


class EconomyStateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EconomyState.objects.all()
    serializer_class = EconomyStateSerializer

    @action(detail=False, methods=['get'])
    def latest(self, request):
        state = EconomyState.objects.order_by('-tick_number').first()
        if not state:
            return Response({'detail': 'No economy state recorded yet.'}, status=404)
        return Response(EconomyStateSerializer(state).data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        limit = int(request.query_params.get('limit', 100))
        states = EconomyState.objects.order_by('-tick_number')[:limit]
        return Response(EconomyStateSerializer(states, many=True).data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer