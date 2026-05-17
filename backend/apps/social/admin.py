from django.contrib import admin
from .models import SocialRelationship


@admin.register(SocialRelationship)
class SocialRelationshipAdmin(admin.ModelAdmin):
    list_display = ['id', 'agent_a', 'agent_b', 'trust_score', 'influence_score', 'relationship_type']
    list_filter = ['relationship_type']
    search_fields = ['agent_a__name', 'agent_b__name']