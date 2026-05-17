from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentViewSet, AgentSocietyView

router = DefaultRouter()
router.register(r'', AgentViewSet, basename='agent')

urlpatterns = [
    path('society/', AgentSocietyView.as_view(), name='agent-society'),
    path('', include(router.urls)),
]