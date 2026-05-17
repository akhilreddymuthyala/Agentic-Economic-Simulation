from rest_framework.views import APIView
from rest_framework.response import Response
from .models import PolicyState
from .serializers import PolicyStateSerializer


class PolicyStateView(APIView):
    def get(self, request):
        policy = PolicyState.get_active()
        return Response(PolicyStateSerializer(policy).data)

    def patch(self, request):
        policy = PolicyState.get_active()
        serializer = PolicyStateSerializer(policy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)