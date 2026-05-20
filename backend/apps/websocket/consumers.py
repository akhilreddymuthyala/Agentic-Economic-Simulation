import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class SimulationConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = 'simulation_broadcast'

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
        logger.info(f'WS client connected: {self.channel_name}')

        # Send full current state on connect so client is immediately up to date
        state = await self.get_full_state()
        await self.send(text_data=json.dumps({
            'type': 'initial_state',
            **state,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)
        logger.info(f'WS client disconnected: {self.channel_name} code={close_code}')

    async def receive(self, text_data):
        """Handle client → server messages."""
        try:
            msg = json.loads(text_data)
            msg_type = msg.get('type')

            if msg_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))

            elif msg_type == 'request_state':
                state = await self.get_full_state()
                await self.send(text_data=json.dumps({
                    'type': 'full_state',
                    **state,
                }))

            elif msg_type == 'request_events':
                events = await self.get_recent_events(
                    limit=msg.get('limit', 50)
                )
                await self.send(text_data=json.dumps({
                    'type': 'event_history',
                    'events': events,
                }))

        except Exception as e:
            logger.error(f'WS receive error: {e}')

    # ── Group message handlers ────────────────────────────────────────────────

    async def simulation_tick(self, event):
        """Forward tick payload to this client."""
        await self.send(text_data=json.dumps(event['payload']))

    async def simulation_event(self, event):
        """Forward event payload to this client."""
        await self.send(text_data=json.dumps(event['payload']))

    async def simulation_status(self, event):
        """Forward status update to this client."""
        await self.send(text_data=json.dumps(event['payload']))

    # ── DB helpers ────────────────────────────────────────────────────────────

    @database_sync_to_async
    def get_full_state(self) -> dict:
        """
        Build a complete state snapshot for new connections.
        Sent once on connect so the client doesn't show blank data.
        """
        from apps.simulation.models import SimulationConfig
        from apps.economy.models import EconomyState
        from apps.policies.models import PolicyState
        from apps.resources.models import ResourceState
        from apps.agents.models import Agent
        from apps.events.models import SimulationEvent
        from django.db.models import Count, Avg

        config = SimulationConfig.get_active()
        latest_eco = EconomyState.get_latest()
        policy = PolicyState.get_active()
        resource = ResourceState.get_active()

        eco_data = {}
        if latest_eco:
            eco_data = {
                'gdp': latest_eco.gdp,
                'gdp_growth_rate': latest_eco.gdp_growth_rate,
                'inflation': latest_eco.inflation,
                'unemployment': latest_eco.unemployment,
                'market_confidence': latest_eco.market_confidence,
                'wealth_gini': latest_eco.wealth_gini,
                'resource_index': latest_eco.resource_index,
                'economic_stability': latest_eco.economic_stability,
            }

        emotion_dist = dict(
            Agent.objects.filter(is_active=True)
            .values_list('dominant_emotion')
            .annotate(count=Count('id'))
            .values_list('dominant_emotion', 'count')
        )

        recent_events = list(
            SimulationEvent.objects.order_by('-tick_number')[:20].values(
                'event_type', 'severity', 'description',
                'simulation_year', 'simulation_month',
                'simulation_day', 'tick_number',
            )
        )

        for evt in recent_events:
            evt['year'] = evt.pop('simulation_year')
            evt['month'] = evt.pop('simulation_month')
            evt['day'] = evt.pop('simulation_day')
            evt['tick'] = evt.pop('tick_number')
            evt['type'] = 'simulation_event'

        return {
            'status': config.status,
            'speed_multiplier': config.speed_multiplier,
            'current_tick': config.current_tick,
            'current_year': config.current_year,
            'current_month': config.current_month,
            'current_day': config.current_day,
            'current_hour': config.current_hour,
            'economy': eco_data,
            'emotion_distribution': emotion_dist,
            'recent_events': recent_events,
            'policy': {
                'tax_rate': policy.tax_rate,
                'interest_rate': policy.interest_rate,
                'government_spending': policy.government_spending,
                'stimulus_active': policy.stimulus_active,
            },
            'resources': {
                'food_supply': resource.food_supply,
                'oil_supply': resource.oil_supply,
                'energy_availability': resource.energy_availability,
                'housing_supply': resource.housing_supply,
                'water_resources': resource.water_resources,
            },
        }

    @database_sync_to_async
    def get_recent_events(self, limit: int = 50) -> list:
        from apps.events.models import SimulationEvent
        events = list(
            SimulationEvent.objects.order_by('-tick_number')[:limit].values(
                'event_type', 'severity', 'description',
                'simulation_year', 'simulation_month',
                'simulation_day', 'tick_number',
            )
        )
        for evt in events:
            evt['year'] = evt.pop('simulation_year')
            evt['month'] = evt.pop('simulation_month')
            evt['day'] = evt.pop('simulation_day')
            evt['tick'] = evt.pop('tick_number')
            evt['type'] = 'simulation_event'
        return events