from django.urls import path
from .views import NeuralLogListView, DecisionSummaryView

urlpatterns = [
    path('neural-logs/', NeuralLogListView.as_view(), name='neural-logs'),
    path('decision-summary/', DecisionSummaryView.as_view(), name='decision-summary'),
]