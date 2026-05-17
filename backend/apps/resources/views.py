from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ResourceState
from .serializers import ResourceStateSerializer


class ResourceStateView(APIView):
    def get(self, request):
        resource = ResourceState.get_active()
        return Response(ResourceStateSerializer(resource).data)

    def patch(self, request):
        resource = ResourceState.get_active()
        serializer = ResourceStateSerializer(resource, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)