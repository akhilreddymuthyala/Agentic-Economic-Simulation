from django.db import models


class AgentEmotionLog(models.Model):
    agent = models.ForeignKey('agents.Agent', on_delete=models.CASCADE, related_name='emotion_logs')
    fear = models.FloatField(default=0.0)
    greed = models.FloatField(default=0.0)
    trust = models.FloatField(default=0.5)
    optimism = models.FloatField(default=0.5)
    stress = models.FloatField(default=0.0)
    panic = models.FloatField(default=0.0)
    dominant_emotion = models.CharField(max_length=20, default='neutral')
    tick_number = models.BigIntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agent_emotion_logs'

    def __str__(self):
        return f'Emotion agent={self.agent_id} tick={self.tick_number}'