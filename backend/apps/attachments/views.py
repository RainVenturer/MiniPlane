# ── 附件视图 ─────────────────────────────────────────────────────
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Attachment
from .serializers import AttachmentSerializer, AttachmentUploadSerializer


@extend_schema_view(
    list=extend_schema(summary="任务附件列表", tags=["附件"]),
    create=extend_schema(summary="上传附件", tags=["附件"]),
    destroy=extend_schema(summary="删除附件", tags=["附件"]),
)
class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return AttachmentUploadSerializer
        return AttachmentSerializer

    def get_queryset(self):
        task_id = self.kwargs.get("task_id")
        return Attachment.objects.filter(task_id=task_id)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.action == "create":
            ctx["task_id"] = self.kwargs.get("task_id")
        return ctx
