# ── 通知视图 ─────────────────────────────────────────────────────
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Notification
from .serializers import NotificationSerializer


@extend_schema_view(
    list=extend_schema(summary="我的通知列表", tags=["通知"]),
    mark_read=extend_schema(summary="标记已读", tags=["通知"]),
    read_all=extend_schema(summary="全部已读", tags=["通知"]),
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
        ).select_related("actor")

    @action(methods=["patch"], detail=True, url_path="read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"detail": "已标记为已读"})

    @action(methods=["post"], detail=False, url_path="read-all")
    def read_all(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"detail": f"已标记 {updated} 条通知为已读"})
