"""
Transaction service — records buy/sell events between agents.
Used by the agent processor to log economic activity.
"""
from apps.economy.models import Transaction


def record_transaction(buyer_id: int, seller_id: int, amount: float,
                       resource: str, context: dict):
    """Create a transaction record for the current tick."""
    Transaction.objects.create(
        buyer_id=buyer_id,
        seller_id=seller_id,
        amount=amount,
        resource=resource,
        simulation_day=context['day'],
        simulation_month=context['month'],
        simulation_year=context['year'],
        tick_number=context['tick'],
    )