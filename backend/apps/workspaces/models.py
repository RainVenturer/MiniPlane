# ── 工作空间模型 ─────────────────────────────────────────────────
from django.db import models
from django.conf import settings
import uuid


class Workspace(models.Model):
    """工作空间 — 团队协作的顶层容器"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("名称", max_length=100)
    slug = models.SlugField("标识", max_length=120, unique=True, db_index=True)
    description = models.TextField("描述", blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="owned_workspaces", verbose_name="所有者",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "工作空间"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class WorkspaceMember(models.Model):
    """工作空间成员与角色"""
    class Role(models.TextChoices):
        ADMIN = "admin", "管理员"
        MEMBER = "member", "普通成员"
        GUEST = "guest", "访客"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE,
        related_name="members", verbose_name="工作空间",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="workspace_memberships", verbose_name="用户",
    )
    role = models.CharField("角色", max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField("加入时间", auto_now_add=True)

    class Meta:
        verbose_name = "工作空间成员"
        verbose_name_plural = verbose_name
        unique_together = [("workspace", "user")]
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user} → {self.workspace} ({self.get_role_display()})"
