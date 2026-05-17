from django.urls import path
from .views import SimulationStatusView, SimulationControlView

urlpatterns = [
    path('status/', SimulationStatusView.as_view(), name='simulation-status'),
    path('control/', SimulationControlView.as_view(), name='simulation-control'),
]