from django.urls import path
from .views import CommentViewSet

urlpatterns = [
    path("", CommentViewSet.as_view({"get": "list"}), name="comment-list"),
    path("<uuid:pk>/", CommentViewSet.as_view({
        "put": "update", "patch": "partial_update", "delete": "destroy",
    }), name="comment-detail"),
]
