from django.urls import path
from .views import SnapshotListView, SnapshotRestoreView

urlpatterns = [
    path('', SnapshotListView.as_view(), name='snapshot-list'),
    path('<int:snapshot_id>/restore/', SnapshotRestoreView.as_view(), name='snapshot-restore'),
]