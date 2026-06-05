from django.urls import path
from .views import ProjectViewSet

urlpatterns = [
    path("", ProjectViewSet.as_view({"get": "list"}), name="project-list"),
    path("<uuid:pk>/", ProjectViewSet.as_view({
        "get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy",
    }), name="project-detail"),
    path("<uuid:pk>/archive/", ProjectViewSet.as_view({"post": "archive"}), name="project-archive"),
    path("<uuid:pk>/restore/", ProjectViewSet.as_view({"post": "restore"}), name="project-restore"),
    path("<uuid:pk>/members/", ProjectViewSet.as_view({
        "get": "members", "post": "members",
    }), name="project-members"),
    path("<uuid:pk>/members/<uuid:uid>/", ProjectViewSet.as_view({
        "delete": "remove_member",
    }), name="project-member-detail"),
]
