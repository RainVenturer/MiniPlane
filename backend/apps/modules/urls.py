from django.urls import path
from .views import ModuleViewSet

urlpatterns = [
    path("", ModuleViewSet.as_view({"get": "list"}), name="module-list"),
    path("<uuid:pk>/", ModuleViewSet.as_view({
        "get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy",
    }), name="module-detail"),
]
