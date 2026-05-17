from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import save_snapshot, restore_snapshot, list_snapshots
from .models import SimulationSnapshot
from rest_framework import serializers


class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationSnapshot
        fields = ['id', 'label', 'tick_number', 'simulation_year',
                  'simulation_month', 'simulation_day', 'created_at']


class SnapshotListView(APIView):
    def get(self, request):
        snapshots = list(list_snapshots())
        return Response(snapshots)

    def post(self, request):
        label = request.data.get('label', '')
        snapshot = save_snapshot(label=label)
        return Response({
            'id': snapshot.id,
            'label': snapshot.label,
            'tick_number': snapshot.tick_number,
        }, status=status.HTTP_201_CREATED)


class SnapshotRestoreView(APIView):
    def post(self, request, snapshot_id):
        success = restore_snapshot(snapshot_id)
        if success:
            return Response({'detail': f'Snapshot {snapshot_id} restored.'})
        return Response(
            {'detail': f'Snapshot {snapshot_id} not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )