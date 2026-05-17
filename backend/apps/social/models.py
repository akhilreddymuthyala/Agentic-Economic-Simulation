from django.db import models


class SocialRelationship(models.Model):
    agent_a = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        related_name='relationships_as_a',
    )
    agent_b = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        related_name='relationships_as_b',
    )
    trust_score = models.FloatField(default=0.5)
    influence_score = models.FloatField(default=0.5)
    relationship_type = models.CharField(max_length=50, default='neutral')
    interaction_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'social_relationships'
        unique_together = [['agent_a', 'agent_b']]
        indexes = [
            models.Index(fields=['agent_a']),
            models.Index(fields=['agent_b']),
        ]

    def __str__(self):
        return f'Rel {self.agent_a_id}<->{self.agent_b_id} trust={self.trust_score:.2f}'