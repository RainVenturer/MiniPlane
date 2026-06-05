from django.urls import path
from .views import IterationViewSet

urlpatterns = [
    path("", IterationViewSet.as_view({"get": "list"}), name="iteration-list"),
    path("<uuid:pk>/", IterationViewSet.as_view({
        "get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy",
    }), name="iteration-detail"),
    path("<uuid:pk>/tasks/", IterationViewSet.as_view({"post": "add_tasks"}), name="iteration-add-tasks"),
]
