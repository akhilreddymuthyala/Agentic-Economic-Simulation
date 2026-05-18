from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from .models import PolicyState
from .serializers import PolicyStateSerializer

POLICY_BOUNDS = {
    'tax_rate': (0.0, 100.0),
    'interest_rate': (0.0, 30.0),
    'government_spending': (0.0, 1_000_000.0),
    'subsidy_level': (0.0, 100_000.0),
    'stimulus_amount': (0.0, 1_000_000.0),
    'market_regulation': (0.0, 100.0),
}


class PolicyStateView(APIView):
    def get(self, request):
        policy = PolicyState.get_active()
        return Response(PolicyStateSerializer(policy).data)

    def patch(self, request):
        policy = PolicyState.get_active()
        data = request.data.copy()

        # Clamp numeric values to valid bounds
        for field, (min_val, max_val) in POLICY_BOUNDS.items():
            if field in data:
                try:
                    data[field] = max(min_val, min(max_val, float(data[field])))
                except (TypeError, ValueError):
                    return Response(
                        {'error': f'Invalid value for {field}'},
                        status=http_status.HTTP_400_BAD_REQUEST,
                    )

        serializer = PolicyStateSerializer(policy, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)