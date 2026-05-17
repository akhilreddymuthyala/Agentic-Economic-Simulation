from django.urls import path
from .views import PolicyStateView

urlpatterns = [
    path('', PolicyStateView.as_view(), name='policy-state'),
]