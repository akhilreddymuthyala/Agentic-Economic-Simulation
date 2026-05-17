from django.db import models


class NeuralLog(models.Model):
    agent = models.ForeignKey('agents.Agent', on_delete=models.CASCADE, related_name='neural_logs')
    decision_input = models.JSONField()
    decision_output = models.CharField(max_length=50)
    confidence = models.FloatField(default=0.0)
    reasoning = models.TextField(blank=True, default='')
    tick_number = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'neural_logs'

    def __str__(self):
        return f'NeuralLog agent={self.agent_id} output={self.decision_output}'