"""
WebSocket 协议路由
"""
from django.urls import path
from apps.notifications.consumers import NotificationConsumer
from apps.projects.consumers import ProjectConsumer

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi(), name="ws-notifications"),
    path("ws/projects/<uuid:project_id>/", ProjectConsumer.as_asgi(), name="ws-project"),
]
