"""
Management command to seed exactly 100 agents with full attributes
and initial social relationships based on profession proximity.

Usage:
    python manage.py seed_agents
    python manage.py seed_agents --reset   (clears existing agents first)
"""
import random
import logging
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.agents.models import Agent, AgentRole, AgentStrategy
from apps.social.models import SocialRelationship
from apps.memory.services import store_memory

logger = logging.getLogger(__name__)

# ── Agent distribution per spec ──────────────────────────────────────────────
AGENT_DISTRIBUTION = [
    (AgentRole.CONSUMER,         35, 3, (500,   3000)),
    (AgentRole.WORKER,           20, 3, (800,   2500)),
    (AgentRole.TRADER,           10, 2, (5000,  20000)),
    (AgentRole.BUSINESS_OWNER,   10, 2, (10000, 50000)),
    (AgentRole.MANUFACTURER,      5, 2, (20000, 80000)),
    (AgentRole.GOVERNMENT,        5, 1, (50000, 100000)),
    (AgentRole.BANKER,            5, 1, (30000, 90000)),
    (AgentRole.INFLUENCER,        5, 1, (5000,  25000)),
    (AgentRole.RESEARCHER,        3, 2, (3000,  10000)),
    (AgentRole.RESOURCE_SUPPLIER, 2, 2, (15000, 60000)),
]

# Name pools
FIRST_NAMES = [
    'Alex', 'Jordan', 'Morgan', 'Taylor', 'Casey', 'Riley', 'Drew', 'Avery',
    'Quinn', 'Blake', 'Cameron', 'Reese', 'Skyler', 'Dakota', 'Hayden',
    'Peyton', 'Finley', 'Rowan', 'Sage', 'Emery', 'Kendall', 'Harley',
    'Logan', 'Parker', 'Reagan', 'Shawn', 'Tatum', 'Bailey', 'Jamie', 'Kai',
    'Lane', 'Nico', 'Remy', 'Scout', 'Storm', 'River', 'West', 'Zion',
    'Nova', 'Ari', 'Sol', 'Echo', 'Onyx', 'Flynn', 'Cruz', 'Eden',
    'Felix', 'Iris', 'Juno', 'Knox',
]

LAST_NAMES = [
    'Marsh', 'Vale', 'Cross', 'Stone', 'Reed', 'Cole', 'Hayes', 'Ward',
    'Knox', 'Beck', 'Ford', 'Shaw', 'Price', 'Hunt', 'Nash', 'Lane',
    'Holt', 'Ross', 'Dean', 'Gray', 'Fox', 'Webb', 'Burns', 'Craig',
    'Quinn', 'Hart', 'Long', 'Boyd', 'Ray', 'Park', 'Chen', 'Kim',
    'Patel', 'Singh', 'Rivera', 'Lopez', 'Martin', 'Clark', 'Lewis', 'Hall',
    'Young', 'Allen', 'Wright', 'Scott', 'Green', 'Adams', 'Baker', 'Diaz',
    'James', 'Evans',
]

# Strategy mapping by role
ROLE_STRATEGY_MAP = {
    AgentRole.CONSUMER:          [AgentStrategy.CONSERVATIVE, AgentStrategy.BALANCED],
    AgentRole.WORKER:            [AgentStrategy.CONSERVATIVE, AgentStrategy.BALANCED],
    AgentRole.TRADER:            [AgentStrategy.AGGRESSIVE, AgentStrategy.SPECULATIVE],
    AgentRole.INVESTOR:          [AgentStrategy.SPECULATIVE, AgentStrategy.AGGRESSIVE],
    AgentRole.BUSINESS_OWNER:    [AgentStrategy.AGGRESSIVE, AgentStrategy.BALANCED],
    AgentRole.MANUFACTURER:      [AgentStrategy.BALANCED, AgentStrategy.CONSERVATIVE],
    AgentRole.GOVERNMENT:        [AgentStrategy.COOPERATIVE, AgentStrategy.BALANCED],
    AgentRole.BANKER:            [AgentStrategy.CONSERVATIVE, AgentStrategy.BALANCED],
    AgentRole.INFLUENCER:        [AgentStrategy.AGGRESSIVE, AgentStrategy.COOPERATIVE],
    AgentRole.RESEARCHER:        [AgentStrategy.COOPERATIVE, AgentStrategy.BALANCED],
    AgentRole.RESOURCE_SUPPLIER: [AgentStrategy.BALANCED, AgentStrategy.CONSERVATIVE],
}

# Profession proximity groups — agents in same group get higher initial trust
PROXIMITY_GROUPS = [
    {AgentRole.CONSUMER, AgentRole.WORKER},
    {AgentRole.TRADER, AgentRole.INVESTOR, AgentRole.BANKER},
    {AgentRole.BUSINESS_OWNER, AgentRole.MANUFACTURER, AgentRole.RESOURCE_SUPPLIER},
    {AgentRole.GOVERNMENT, AgentRole.RESEARCHER},
    {AgentRole.INFLUENCER},
]

# Initial memory templates per role
ROLE_MEMORIES = {
    AgentRole.CONSUMER:          ('Started my life in this economy with basic savings.', 0.3),
    AgentRole.WORKER:            ('Secured my first job. Hoping wages improve over time.', 0.3),
    AgentRole.TRADER:            ('Entered the market. Watching price signals carefully.', 0.5),
    AgentRole.INVESTOR:          ('Allocated initial capital across several opportunities.', 0.5),
    AgentRole.BUSINESS_OWNER:    ('Launched my business. Hired first employees today.', 0.6),
    AgentRole.MANUFACTURER:      ('Production line is running. Resource costs are manageable.', 0.5),
    AgentRole.GOVERNMENT:        ('Assumed office. Economy needs careful stewardship.', 0.7),
    AgentRole.BANKER:            ('Opened the vault. Ready to provide liquidity to the market.', 0.6),
    AgentRole.INFLUENCER:        ('Built my network. My voice can move markets.', 0.6),
    AgentRole.RESEARCHER:        ('Research underway. Innovation takes time but pays off.', 0.5),
    AgentRole.RESOURCE_SUPPLIER: ('Supply chain established. Watching scarcity signals.', 0.5),
}


def get_proximity_group(role):
    for group in PROXIMITY_GROUPS:
        if role in group:
            return group
    return set()


def generate_name(used_names):
    for _ in range(200):
        name = f'{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}'
        if name not in used_names:
            used_names.add(name)
            return name
    return f'Agent_{random.randint(1000, 9999)}'


class Command(BaseCommand):
    help = 'Seed 100 agents with full attributes and initial social relationships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing agents before seeding',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting agents, relationships and memories...')
            SocialRelationship.objects.all().delete()
            from apps.memory.models import AgentMemory
            AgentMemory.objects.all().delete()
            Agent.objects.all().delete()
            self.stdout.write(self.style.WARNING('All agents cleared.'))

        existing = Agent.objects.count()
        if existing >= 100:
            self.stdout.write(self.style.WARNING(
                f'{existing} agents already exist. Use --reset to reseed.'
            ))
            return

        self.stdout.write('Seeding 100 agents...')

        agents = []
        used_names = set()

        with transaction.atomic():
            for role, count, tier, wealth_range in AGENT_DISTRIBUTION:
                strategies = ROLE_STRATEGY_MAP.get(role, [AgentStrategy.BALANCED])

                for i in range(count):
                    name = generate_name(used_names)
                    wealth = round(random.uniform(*wealth_range), 2)
                    strategy = random.choice(strategies)

                    # Role-specific emotion defaults
                    base_trust = random.uniform(0.3, 0.7)
                    base_optimism = random.uniform(0.3, 0.7)
                    base_fear = random.uniform(0.0, 0.2)
                    base_greed = random.uniform(0.1, 0.4) if role in {
                        AgentRole.TRADER, AgentRole.INVESTOR, AgentRole.BUSINESS_OWNER
                    } else random.uniform(0.0, 0.2)

                    risk_score = random.uniform(0.6, 0.9) if role in {
                        AgentRole.TRADER, AgentRole.INVESTOR, AgentRole.BUSINESS_OWNER
                    } else random.uniform(0.2, 0.6)

                    social_influence = random.uniform(0.7, 1.0) if role in {
                        AgentRole.INFLUENCER, AgentRole.GOVERNMENT
                    } else random.uniform(0.1, 0.5)

                    agent = Agent(
                        name=name,
                        profession=role,
                        intelligence_tier=tier,
                        wealth=wealth,
                        income=round(wealth * random.uniform(0.01, 0.05), 2),
                        debt=round(wealth * random.uniform(0.0, 0.3), 2),
                        emotion_fear=round(base_fear, 3),
                        emotion_greed=round(base_greed, 3),
                        emotion_trust=round(base_trust, 3),
                        emotion_optimism=round(base_optimism, 3),
                        emotion_stress=round(random.uniform(0.0, 0.2), 3),
                        emotion_panic=0.0,
                        dominant_emotion='neutral',
                        risk_score=round(risk_score, 3),
                        strategy=strategy,
                        social_influence=round(social_influence, 3),
                        cooperation_rate=round(random.uniform(0.3, 0.8), 3),
                        is_employed=role not in {AgentRole.CONSUMER},
                        is_active=True,
                        last_action='initialized',
                    )
                    agents.append(agent)

            created_agents = Agent.objects.bulk_create(agents)
            self.stdout.write(f'  Created {len(created_agents)} agents.')

            # ── Update dominant emotion for each ─────────────────────────────
            for agent in created_agents:
                agent.dominant_emotion = agent.compute_dominant_emotion()
            Agent.objects.bulk_update(created_agents, ['dominant_emotion'])
            self.stdout.write('  Dominant emotions computed.')

            # ── Seed initial memories ────────────────────────────────────────
            self.stdout.write('  Seeding initial memories...')
            for agent in created_agents:
                mem_text, importance = ROLE_MEMORIES.get(
                    agent.profession,
                    ('Entered the simulation.', 0.3)
                )
                store_memory(
                    agent_id=agent.id,
                    text=mem_text,
                    importance=importance,
                    memory_type='origin',
                    tick=0,
                    sim_day=1,
                    sim_year=1,
                )
            self.stdout.write('  Initial memories stored.')

            # ── Seed social relationships ────────────────────────────────────
            self.stdout.write('  Building social relationships...')
            relationships = []
            agent_list = list(created_agents)

            for i, agent_a in enumerate(agent_list):
                group_a = get_proximity_group(agent_a.profession)

                # Each agent connects to 3–8 others
                num_connections = random.randint(3, 8)
                candidates = [a for a in agent_list if a.id != agent_a.id]
                targets = random.sample(candidates, min(num_connections, len(candidates)))

                for agent_b in targets:
                    # Avoid duplicate pairs — always store with lower id first
                    a, b = sorted([agent_a, agent_b], key=lambda x: x.id)

                    already = any(
                        (r.agent_a_id == a.id and r.agent_b_id == b.id)
                        for r in relationships
                    )
                    if already:
                        continue

                    same_group = agent_b.profession in group_a
                    trust = round(random.uniform(0.5, 0.8) if same_group else random.uniform(0.2, 0.5), 3)
                    influence = round(random.uniform(0.4, 0.7) if same_group else random.uniform(0.1, 0.4), 3)
                    rel_type = 'colleague' if same_group else 'acquaintance'

                    relationships.append(SocialRelationship(
                        agent_a=a,
                        agent_b=b,
                        trust_score=trust,
                        influence_score=influence,
                        relationship_type=rel_type,
                        interaction_count=random.randint(0, 10),
                    ))

            SocialRelationship.objects.bulk_create(relationships, ignore_conflicts=True)
            self.stdout.write(f'  Created {len(relationships)} social relationships.')

        self.stdout.write(self.style.SUCCESS(
            f'\nPhase 2 seeding complete.\n'
            f'  Agents:        {Agent.objects.count()}\n'
            f'  Relationships: {SocialRelationship.objects.count()}\n'
            f'  Memories:      {Agent.objects.count()} (1 per agent)\n'
        ))