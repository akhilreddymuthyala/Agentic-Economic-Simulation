"""
Full simulation reset — restores all agents, economy, policies,
and resources to healthy baseline values.
"""
import random
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Reset simulation to healthy baseline values'

    def handle(self, *args, **options):
        with transaction.atomic():
            self._reset_economy()
            self._reset_policies()
            self._reset_resources()
            self._reset_agents()
            self._reset_simulation_config()

        self.stdout.write(self.style.SUCCESS('Simulation reset complete.'))

    def _reset_economy(self):
        from apps.economy.models import EconomyState
        EconomyState.objects.create(
            gdp=100000.0, gdp_growth_rate=0.0,
            inflation=2.5, unemployment=5.0,
            market_confidence=70.0, wealth_gini=0.35,
            resource_index=85.0, economic_stability=75.0,
            total_money_supply=500000.0, total_wealth=500000.0,
            tick_number=999999999,
            simulation_hour=0, simulation_day=1,
            simulation_month=1, simulation_year=1,
        )
        self.stdout.write('  Economy reset.')

    def _reset_policies(self):
        from apps.policies.models import PolicyState
        PolicyState.objects.filter(pk=1).update(
            tax_rate=20.0, interest_rate=5.0,
            government_spending=10000.0, subsidy_level=0.0,
            stimulus_active=False, stimulus_amount=0.0,
            market_regulation=50.0,
        )
        self.stdout.write('  Policies reset.')

    def _reset_resources(self):
        from apps.resources.models import ResourceState
        ResourceState.objects.filter(pk=1).update(
            food_supply=85.0, oil_supply=80.0,
            energy_availability=82.0, housing_supply=75.0,
            water_resources=90.0,
            food_price=10.0, oil_price=50.0,
            energy_price=30.0, housing_price=200.0,
            water_price=5.0,
        )
        self.stdout.write('  Resources reset.')

    def _reset_agents(self):
        from apps.agents.models import Agent, AgentRole
        from apps.emotions.engine import compute_dominant_emotion

        # Wealth baselines per role
        WEALTH_RANGES = {
            AgentRole.CONSUMER: (500, 3000),
            AgentRole.WORKER: (800, 2500),
            AgentRole.TRADER: (5000, 20000),
            AgentRole.INVESTOR: (5000, 20000),
            AgentRole.BUSINESS_OWNER: (10000, 50000),
            AgentRole.MANUFACTURER: (20000, 80000),
            AgentRole.GOVERNMENT: (50000, 100000),
            AgentRole.BANKER: (30000, 90000),
            AgentRole.INFLUENCER: (5000, 25000),
            AgentRole.RESEARCHER: (3000, 10000),
            AgentRole.RESOURCE_SUPPLIER: (15000, 60000),
        }

        agents = list(Agent.objects.filter(is_active=True))
        for agent in agents:
            lo, hi = WEALTH_RANGES.get(agent.profession, (1000, 5000))
            agent.wealth = round(random.uniform(lo, hi), 2)

            # Reset emotions to varied baseline
            agent.emotion_fear = round(random.uniform(0.05, 0.25), 3)
            agent.emotion_greed = round(random.uniform(0.10, 0.35), 3)
            agent.emotion_trust = round(random.uniform(0.35, 0.65), 3)
            agent.emotion_optimism = round(random.uniform(0.25, 0.50), 3)
            agent.emotion_stress = round(random.uniform(0.05, 0.25), 3)
            agent.emotion_panic = round(random.uniform(0.01, 0.08), 3)
            agent.dominant_emotion = compute_dominant_emotion(
                agent.emotion_fear, agent.emotion_greed,
                agent.emotion_trust, agent.emotion_optimism,
                agent.emotion_stress, agent.emotion_panic,
            )
            agent.last_action = 'reset'
            agent.is_employed = agent.profession != AgentRole.CONSUMER

        Agent.objects.bulk_update(agents, [
            'wealth', 'emotion_fear', 'emotion_greed', 'emotion_trust',
            'emotion_optimism', 'emotion_stress', 'emotion_panic',
            'dominant_emotion', 'last_action', 'is_employed',
        ])
        self.stdout.write(f'  {len(agents)} agents reset.')

    def _reset_simulation_config(self):
        from apps.simulation.models import SimulationConfig, SimulationStatus
        config = SimulationConfig.get_active()
        config.status = SimulationStatus.IDLE
        config.speed_multiplier = 1
        config.reset_clock()
        config.celery_task_id = ''
        config.save()
        self.stdout.write('  Simulation config reset.')