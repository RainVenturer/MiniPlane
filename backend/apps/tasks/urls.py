from django.urls import path
from .views import TaskViewSet

urlpatterns = [
    path("", TaskViewSet.as_view({"get": "list"}), name="task-list"),
    path("<uuid:pk>/", TaskViewSet.as_view({
        "get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy",
    }), name="task-detail"),
    path("<uuid:pk>/status/", TaskViewSet.as_view({"patch": "change_status"}), name="task-status"),
    path("<uuid:pk>/subtasks/", TaskViewSet.as_view({"post": "subtasks"}), name="task-subtasks"),
]
