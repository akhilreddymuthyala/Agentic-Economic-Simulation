from django.urls import path
from .views import ResourceStateView

urlpatterns = [
    path('', ResourceStateView.as_view(), name='resource-state'),
]