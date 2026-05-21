"""
Integration test — verifies all systems are connected and working.
Run after deployment or after major changes.

Usage: python manage.py integration_test
"""
import time
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run integration tests on all simulation components'

    def handle(self, *args, **options):
        self.stdout.write('\n=== Emergent AI Economy — Integration Test ===\n')
        results = []

        results.append(self._test_database())
        results.append(self._test_redis())
        results.append(self._test_celery())
        results.append(self._test_agents())
        results.append(self._test_economy_engine())
        results.append(self._test_emotion_engine())
        results.append(self._test_circulation())
        results.append(self._test_event_detection())
        results.append(self._test_neural_model())
        results.append(self._test_websocket_layer())
        results.append(self._test_snapshot())

        passed = sum(1 for r in results if r)
        failed = len(results) - passed

        self.stdout.write(f'\n=== Results: {passed} passed, {failed} failed ===\n')
        if failed > 0:
            self.stdout.write(self.style.ERROR('Some tests failed — check logs above.'))
        else:
            self.stdout.write(self.style.SUCCESS('All integration tests passed.'))

    def _ok(self, msg):
        self.stdout.write(self.style.SUCCESS(f'  ✓ {msg}'))
        return True

    def _fail(self, msg, err=''):
        self.stdout.write(self.style.ERROR(f'  ✗ {msg}: {err}'))
        return False

    def _test_database(self):
        self.stdout.write('Database...')
        try:
            from apps.agents.models import Agent
            count = Agent.objects.count()
            if count < 100:
                return self._fail('Agent count', f'only {count} agents (need 100)')
            return self._ok(f'{count} agents in database')
        except Exception as e:
            return self._fail('Database connection', str(e))

    def _test_redis(self):
        self.stdout.write('Redis...')
        try:
            from django.core.cache import cache
            cache.set('integration_test', 'ok', 5)
            val = cache.get('integration_test')
            if val != 'ok':
                return self._fail('Redis read/write')
            return self._ok('Redis read/write working')
        except Exception as e:
            return self._fail('Redis', str(e))

    def _test_celery(self):
        self.stdout.write('Celery...')
        try:
            from apps.simulation.tasks import verify_celery
            result = verify_celery.apply_async()
            val = result.get(timeout=8)
            if val != 'Celery OK':
                return self._fail('Celery task result', str(val))
            return self._ok('Celery task execution working')
        except Exception as e:
            return self._fail('Celery', str(e))

    def _test_agents(self):
        self.stdout.write('Agent system...')
        try:
            from apps.agents.models import Agent, AgentRole
            distribution = {
                role: Agent.objects.filter(profession=role).count()
                for role in AgentRole.values
            }
            total = sum(distribution.values())
            if total < 100:
                return self._fail('Agent distribution', f'{total} agents')

            from apps.social.models import SocialRelationship
            rel_count = SocialRelationship.objects.count()
            if rel_count < 50:
                return self._fail('Social relationships', f'only {rel_count}')

            return self._ok(f'100 agents, {rel_count} relationships')
        except Exception as e:
            return self._fail('Agent system', str(e))

    def _test_economy_engine(self):
        self.stdout.write('Economy engine...')
        try:
            from apps.economy.models import EconomyState
            from apps.policies.models import PolicyState
            from apps.resources.models import ResourceState

            PolicyState.get_active()
            ResourceState.get_active()
            latest = EconomyState.get_latest()

            if not latest:
                return self._fail('No economy state recorded')

            if latest.gdp <= 0:
                return self._fail('GDP is zero or negative')

            return self._ok(f'Economy state: GDP={latest.gdp:.0f} Inflation={latest.inflation:.1f}%')
        except Exception as e:
            return self._fail('Economy engine', str(e))

    def _test_emotion_engine(self):
        self.stdout.write('Emotion engine...')
        try:
            from apps.agents.models import Agent
            from apps.emotions.engine import compute_economy_triggers, run_emotion_engine

            # Build mock context
            context = {
                'tick': 999,
                'year': 1, 'month': 1, 'day': 1, 'hour': 0,
                'economy': {
                    'gdp': 100000, 'gdp_growth_rate': 1.0,
                    'inflation': 8.0, 'unemployment': 20.0,
                    'market_confidence': 35.0,
                    'economic_stability': 40.0,
                },
                'resource_shortages': [{'resource': 'oil', 'supply': 10}],
                'agent_updates': [],
                'events_detected': [],
            }

            deltas = compute_economy_triggers(context)
            assert deltas['fear'] > 0, 'Fear should increase with bad economy'
            assert deltas['stress'] > 0, 'Stress should increase with high unemployment'

            return self._ok(f'Emotion triggers: fear_delta={deltas["fear"]:.4f}')
        except Exception as e:
            return self._fail('Emotion engine', str(e))

    def _test_circulation(self):
        self.stdout.write('Circulation engine...')
        try:
            from apps.agents.models import Agent

            before = Agent.objects.filter(profession='government').aggregate(
                total=__import__('django.db.models', fromlist=['Sum']).Sum('wealth')
            )['total'] or 0

            context = {
                'tick': 4,  # divisible by CIRCULATION_INTERVAL
                'year': 1, 'month': 1, 'day': 1, 'hour': 0,
                'economy': {
                    'gdp': 100000, 'gdp_growth_rate': 1.0,
                    'inflation': 3.0, 'unemployment': 5.0,
                    'market_confidence': 70.0,
                },
                'resource_shortages': [],
                'policy_state': {'tax_rate': 20.0},
            }

            from apps.economy.circulation import run_circulation
            run_circulation(context)

            after = Agent.objects.filter(profession='government').aggregate(
                total=__import__('django.db.models', fromlist=['Sum']).Sum('wealth')
            )['total'] or 0

            return self._ok(f'Circulation ran. Gov wealth: {before:.0f} → {after:.0f}')
        except Exception as e:
            return self._fail('Circulation', str(e))

    def _test_event_detection(self):
        self.stdout.write('Event detection...')
        try:
            from apps.events.engine import run_event_detection

            context = {
                'tick': 100,
                'year': 1, 'month': 1, 'day': 5, 'hour': 0,
                'economy': {
                    'gdp': 80000, 'gdp_growth_rate': -2.0,
                    'inflation': 25.0, 'unemployment': 30.0,
                    'market_confidence': 25.0,
                    'economic_stability': 20.0,
                },
                'resource_shortages': [{'resource': 'oil', 'supply': 5}],
                'events_detected': [],
                'agent_updates': [],
            }

            result = run_event_detection(context)
            event_count = len(result.get('events_detected', []))
            return self._ok(f'Event detection ran — {event_count} events detected in stress test')
        except Exception as e:
            return self._fail('Event detection', str(e))

    def _test_neural_model(self):
        self.stdout.write('Neural model...')
        try:
            from apps.ai.neural_model import get_model, ACTIONS
            model = get_model()
            assert model is not None, 'Model is None'

            import torch
            test_input = torch.zeros(1, 13)
            with torch.no_grad():
                output = model(test_input)
            assert output.shape[1] == len(ACTIONS), f'Wrong output shape: {output.shape}'

            return self._ok(f'Neural model inference working ({len(ACTIONS)} actions)')
        except Exception as e:
            return self._fail('Neural model', str(e))

    def _test_websocket_layer(self):
        self.stdout.write('WebSocket layer...')
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            assert channel_layer is not None, 'No channel layer'

            # Test group send (won't fail even if no clients connected)
            async_to_sync(channel_layer.group_send)(
                'simulation_broadcast',
                {'type': 'simulation_tick', 'payload': {'type': 'test'}}
            )
            return self._ok('WebSocket channel layer working')
        except Exception as e:
            return self._fail('WebSocket layer', str(e))

    def _test_snapshot(self):
        self.stdout.write('Snapshot system...')
        try:
            from apps.snapshots.services import save_snapshot, restore_snapshot, list_snapshots

            snapshot = save_snapshot(label='integration_test')
            assert snapshot.id is not None

            snapshots = list(list_snapshots())
            assert len(snapshots) > 0

            success = restore_snapshot(snapshot.id)
            assert success, 'Restore returned False'

            return self._ok(f'Snapshot save/restore working (id={snapshot.id})')
        except Exception as e:
            return self._fail('Snapshot system', str(e))