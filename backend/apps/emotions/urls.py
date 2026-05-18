from django.urls import path
from .views import EmotionDistributionView, AgentEmotionHistoryView

urlpatterns = [
    path('distribution/', EmotionDistributionView.as_view(), name='emotion-distribution'),
    path('agent/<int:agent_id>/history/', AgentEmotionHistoryView.as_view(), name='agent-emotion-history'),
]