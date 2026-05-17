"""
Snapshot manager — save, restore, and list simulation states.
Serialises: SimulationConfig, EconomyState (latest), all Agents,
all SocialRelationships.
"""
import json
import logging
from django.db import transaction

logger = logging.getLogger(__name__)


def save_snapshot(label: str = '') -> 'SimulationSnapshot':
    from apps.snapshots.models import SimulationSnapshot
    from apps.simulation.models import SimulationConfig
    from apps.economy.models import EconomyState
    from apps.agents.models import Agent
    from apps.social.models import SocialRelationship

    config = SimulationConfig.get_active()
    latest_economy = EconomyState.get_latest()

    agents_data = list(
        Agent.objects.filter(is_active=True).values(
            'id', 'name', 'profession', 'intelligence_tier',
            'wealth', 'income', 'debt',
            'emotion_fear', 'emotion_greed', 'emotion_trust',
            'emotion_optimism', 'emotion_stress', 'emotion_panic',
            'dominant_emotion', 'risk_score', 'strategy',
            'social_influence', 'cooperation_rate',
            'is_employed', 'is_active', 'last_action',
        )
    )

    relationships_data = list(
        SocialRelationship.objects.all().values(
            'agent_a_id', 'agent_b_id', 'trust_score',
            'influence_score', 'relationship_type', 'interaction_count',
        )
    )

    economy_data = {}
    if latest_economy:
        economy_data = {
            'gdp': latest_economy.gdp,
            'gdp_growth_rate': latest_economy.gdp_growth_rate,
            'inflation': latest_economy.inflation,
            'unemployment': latest_economy.unemployment,
            'market_confidence': latest_economy.market_confidence,
            'wealth_gini': latest_economy.wealth_gini,
            'resource_index': latest_economy.resource_index,
            'economic_stability': latest_economy.economic_stability,
            'total_money_supply': latest_economy.total_money_supply,
            'total_wealth': latest_economy.total_wealth,
        }

    state_data = {
        'config': {
            'status': config.status,
            'speed_multiplier': config.speed_multiplier,
            'current_tick': config.current_tick,
            'current_hour': config.current_hour,
            'current_day': config.current_day,
            'current_week': config.current_week,
            'current_month': config.current_month,
            'current_year': config.current_year,
        },
        'economy': economy_data,
        'agents': agents_data,
        'relationships': relationships_data,
    }

    snapshot = SimulationSnapshot.objects.create(
        label=label or f'Snapshot at tick {config.current_tick}',
        tick_number=config.current_tick,
        simulation_day=config.current_day,
        simulation_month=config.current_month,
        simulation_year=config.current_year,
        state_data=state_data,
    )

    logger.info(f'Snapshot saved: id={snapshot.id} tick={config.current_tick}')
    return snapshot


def restore_snapshot(snapshot_id: int) -> bool:
    from apps.snapshots.models import SimulationSnapshot
    from apps.simulation.models import SimulationConfig, SimulationStatus
    from apps.economy.models import EconomyState
    from apps.agents.models import Agent
    from apps.social.models import SocialRelationship

    try:
        snapshot = SimulationSnapshot.objects.get(pk=snapshot_id)
    except SimulationSnapshot.DoesNotExist:
        logger.error(f'Snapshot {snapshot_id} not found.')
        return False

    data = snapshot.state_data

    with transaction.atomic():
        # Restore config
        config = SimulationConfig.get_active()
        cfg = data['config']
        config.status = SimulationStatus.PAUSED
        config.speed_multiplier = cfg['speed_multiplier']
        config.current_tick = cfg['current_tick']
        config.current_hour = cfg['current_hour']
        config.current_day = cfg['current_day']
        config.current_week = cfg.get('current_week', 1)
        config.current_month = cfg['current_month']
        config.current_year = cfg['current_year']
        config.save()

        # Restore economy snapshot
        eco = data.get('economy', {})
        if eco:
            EconomyState.objects.create(
                tick_number=cfg['current_tick'],
                simulation_hour=cfg['current_hour'],
                simulation_day=cfg['current_day'],
                simulation_month=cfg['current_month'],
                simulation_year=cfg['current_year'],
                **eco,
            )

        # Restore agent states
        for agent_data in data.get('agents', []):
            agent_id = agent_data.pop('id')
            Agent.objects.filter(pk=agent_id).update(**agent_data)

        # Restore relationships
        SocialRelationship.objects.all().delete()
        rel_objs = []
        for rel in data.get('relationships', []):
            rel_objs.append(SocialRelationship(
                agent_a_id=rel['agent_a_id'],
                agent_b_id=rel['agent_b_id'],
                trust_score=rel['trust_score'],
                influence_score=rel['influence_score'],
                relationship_type=rel['relationship_type'],
                interaction_count=rel['interaction_count'],
            ))
        SocialRelationship.objects.bulk_create(rel_objs, ignore_conflicts=True)

    logger.info(f'Snapshot {snapshot_id} restored successfully.')
    return True


def list_snapshots():
    from apps.snapshots.models import SimulationSnapshot
    return SimulationSnapshot.objects.order_by('-tick_number').values(
        'id', 'label', 'tick_number',
        'simulation_year', 'simulation_month', 'simulation_day',
        'created_at',
    )