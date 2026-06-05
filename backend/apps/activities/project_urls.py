from django.urls import path
from .views import ActivityViewSet

urlpatterns = [
    path("", ActivityViewSet.as_view({"get": "list"}), name="project-activity-list"),
]
