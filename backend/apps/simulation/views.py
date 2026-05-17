from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SimulationConfig, SimulationStatus
from .serializers import SimulationConfigSerializer


class SimulationStatusView(APIView):
    def get(self, request):
        config = SimulationConfig.get_active()
        return Response(SimulationConfigSerializer(config).data)


class SimulationControlView(APIView):
    VALID_SPEEDS = [1, 5, 10, 25, 50]

    def post(self, request):
        action = request.data.get('action')
        config = SimulationConfig.get_active()

        if action == 'start':
            config.status = SimulationStatus.RUNNING
        elif action == 'pause':
            config.status = SimulationStatus.PAUSED
        elif action == 'stop':
            config.status = SimulationStatus.STOPPED
        elif action == 'reset':
            config.status = SimulationStatus.IDLE
            config.current_tick = 0
            config.current_day = 1
            config.current_month = 1
            config.current_year = 1
            config.current_hour = 0
        elif action == 'set_speed':
            speed = int(request.data.get('speed', 1))
            if speed not in self.VALID_SPEEDS:
                return Response(
                    {'error': f'Speed must be one of {self.VALID_SPEEDS}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            config.speed_multiplier = speed
        else:
            return Response(
                {'error': f'Unknown action: {action}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        config.save()
        return Response(SimulationConfigSerializer(config).data)