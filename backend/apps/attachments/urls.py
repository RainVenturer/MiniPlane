from django.urls import path
from .views import AttachmentViewSet

urlpatterns = [
    path("<uuid:pk>/", AttachmentViewSet.as_view({
        "delete": "destroy",
    }), name="attachment-detail"),
]
