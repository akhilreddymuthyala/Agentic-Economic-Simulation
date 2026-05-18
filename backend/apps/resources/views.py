from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from .models import ResourceState
from .serializers import ResourceStateSerializer

RESOURCE_BOUNDS = {
    'food_supply': (0.0, 100.0),
    'oil_supply': (0.0, 100.0),
    'energy_availability': (0.0, 100.0),
    'housing_supply': (0.0, 100.0),
    'water_resources': (0.0, 100.0),
}


class ResourceStateView(APIView):
    def get(self, request):
        resource = ResourceState.get_active()
        return Response(ResourceStateSerializer(resource).data)

    def patch(self, request):
        resource = ResourceState.get_active()
        data = request.data.copy()

        for field, (min_val, max_val) in RESOURCE_BOUNDS.items():
            if field in data:
                try:
                    data[field] = max(min_val, min(max_val, float(data[field])))
                except (TypeError, ValueError):
                    return Response(
                        {'error': f'Invalid value for {field}'},
                        status=http_status.HTTP_400_BAD_REQUEST,
                    )

        serializer = ResourceStateSerializer(resource, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)