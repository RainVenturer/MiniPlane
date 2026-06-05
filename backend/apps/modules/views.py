# ── 模块视图 ─────────────────────────────────────────────────────
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Module
from .serializers import ModuleSerializer, ModuleCreateSerializer


@extend_schema_view(
    list=extend_schema(summary="模块列表", tags=["模块"]),
    create=extend_schema(summary="创建模块", tags=["模块"]),
    retrieve=extend_schema(summary="模块详情", tags=["模块"]),
    update=extend_schema(summary="编辑模块", tags=["模块"]),
    destroy=extend_schema(summary="删除模块", tags=["模块"]),
)
class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ModuleCreateSerializer
        return ModuleSerializer

    def get_queryset(self):
        project_id = self.kwargs.get("proj_id")
        return Module.objects.filter(project_id=project_id)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.action == "create":
            ctx["project_id"] = self.kwargs.get("proj_id")
        return ctx
