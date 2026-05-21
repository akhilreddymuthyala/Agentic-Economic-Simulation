from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='agent',
            index=models.Index(fields=['profession', 'is_active'], name='agent_prof_active_idx'),
        ),
        migrations.AddIndex(
            model_name='agent',
            index=models.Index(fields=['dominant_emotion', 'is_active'], name='agent_emotion_active_idx'),
        ),
        migrations.AddIndex(
            model_name='agent',
            index=models.Index(fields=['intelligence_tier', 'is_active'], name='agent_tier_active_idx'),
        ),
        migrations.AddIndex(
            model_name='agent',
            index=models.Index(fields=['wealth'], name='agent_wealth_idx'),
        ),
    ]