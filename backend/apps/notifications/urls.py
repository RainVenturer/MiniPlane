from django.urls import path
from .views import NotificationViewSet

urlpatterns = [
    path("", NotificationViewSet.as_view({"get": "list"}), name="notification-list"),
    path("<uuid:pk>/read/", NotificationViewSet.as_view({"patch": "mark_read"}), name="notification-read"),
    path("read-all/", NotificationViewSet.as_view({"post": "read_all"}), name="notification-read-all"),
]
