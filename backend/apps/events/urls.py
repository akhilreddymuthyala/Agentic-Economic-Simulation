from django.urls import path
from .views import EventListView, EventSummaryView

urlpatterns = [
    path('', EventListView.as_view(), name='event-list'),
    path('summary/', EventSummaryView.as_view(), name='event-summary'),
]