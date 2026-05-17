from django.db import models
from pgvector.django import VectorField


class AgentMemory(models.Model):
    agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        related_name='memories',
    )
    memory_text = models.TextField()

    # 384-dim embedding — matches all-MiniLM-L6-v2 sentence-transformers model
    # We use a lightweight local embedding in Phase 2; swap for OpenAI in Phase 6
    embedding = VectorField(dimensions=384, null=True, blank=True)

    importance = models.FloatField(default=0.5)
    memory_type = models.CharField(max_length=50, default='experience')
    tick_number = models.BigIntegerField(default=0)
    simulation_day = models.IntegerField(default=1)
    simulation_year = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agent_memories'
        ordering = ['-importance', '-tick_number']
        indexes = [
            models.Index(fields=['agent', 'importance']),
            models.Index(fields=['agent', 'tick_number']),
        ]

    def __str__(self):
        return f'Memory agent={self.agent_id} importance={self.importance:.2f}'