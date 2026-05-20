import json
from channels.generic.websocket import AsyncWebsocketConsumer


class SimulationConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = 'simulation_broadcast'

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to Emergent AI Economy Simulator',
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        pass

    async def simulation_tick(self, event):
        await self.send(text_data=json.dumps(event['payload']))

    async def simulation_event(self, event):
        await self.send(text_data=json.dumps(event['payload']))