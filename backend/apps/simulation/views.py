import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SimulationConfig, SimulationStatus
from .serializers import SimulationConfigSerializer
from .clock import tick_interval_seconds, format_sim_date

logger = logging.getLogger(__name__)

VALID_SPEEDS = [1, 5, 10, 25, 50]


class SimulationStatusView(APIView):
    def get(self, request):
        config = SimulationConfig.get_active()
        data = SimulationConfigSerializer(config).data
        data['tick_interval_seconds'] = tick_interval_seconds(config.speed_multiplier)
        data['formatted_date'] = format_sim_date(config.current_tick)
        return Response(data)


class SimulationControlView(APIView):
    def post(self, request):
        action = request.data.get('action')
        config = SimulationConfig.get_active()

        if action == 'start':
            if config.status == SimulationStatus.RUNNING:
                return Response({'detail': 'Already running.'})
            config.status = SimulationStatus.RUNNING
            config.save()
            # Fire the first tick — subsequent ticks self-schedule
            from apps.simulation.tasks import run_simulation_tick
            task = run_simulation_tick.apply_async(countdown=0)
            config.celery_task_id = task.id
            config.save(update_fields=['celery_task_id'])
            logger.info(f'Simulation started. Task id={task.id}')
            return Response(SimulationConfigSerializer(config).data)

        elif action == 'pause':
            config.status = SimulationStatus.PAUSED
            config.save()
            logger.info('Simulation paused.')
            return Response(SimulationConfigSerializer(config).data)

        elif action == 'stop':
            config.status = SimulationStatus.STOPPED
            config.save()
            logger.info('Simulation stopped.')
            return Response(SimulationConfigSerializer(config).data)

        elif action == 'reset':
            config.status = SimulationStatus.IDLE
            config.reset_clock()
            config.celery_task_id = ''
            config.save()
            logger.info('Simulation reset.')
            return Response(SimulationConfigSerializer(config).data)

        elif action == 'set_speed':
            speed = int(request.data.get('speed', 1))
            if speed not in VALID_SPEEDS:
                return Response(
                    {'error': f'Speed must be one of {VALID_SPEEDS}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            config.speed_multiplier = speed
            config.save(update_fields=['speed_multiplier'])
            return Response({
                **SimulationConfigSerializer(config).data,
                'tick_interval_seconds': tick_interval_seconds(speed),
            })

        else:
            return Response(
                {'error': f'Unknown action: {action}'},
                status=status.HTTP_400_BAD_REQUEST,
            )