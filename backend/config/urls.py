from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/agents/', include('apps.agents.urls')),
    path('api/economy/', include('apps.economy.urls')),
    path('api/simulation/', include('apps.simulation.urls')),
    path('api/policies/', include('apps.policies.urls')),
    path('api/resources/', include('apps.resources.urls')),
]