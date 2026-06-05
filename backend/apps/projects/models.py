# ── 项目模型 ─────────────────────────────────────────────────────
from django.db import models
from django.conf import settings
import uuid


class Project(models.Model):
    """项目 — 归属于工作空间"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.CASCADE,
        related_name="projects", verbose_name="工作空间",
    )
    name = models.CharField("名称", max_length=200)
    identifier = models.CharField("标识符", max_length=12, db_index=True)
    description = models.TextField("描述", blank=True, default="")
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="led_projects", verbose_name="项目负责人",
    )
    is_archived = models.BooleanField("已归档", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "项目"
        verbose_name_plural = verbose_name
        unique_together = [("workspace", "identifier")]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace", "is_archived"]),
        ]

    def __str__(self):
        return f"{self.workspace.name}/{self.name}"


class ProjectMember(models.Model):
    """项目成员角色"""
    class Role(models.TextChoices):
        ADMIN = "admin", "管理员"
        MEMBER = "member", "普通成员"
        VIEWER = "viewer", "只读"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        related_name="members", verbose_name="项目",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="project_memberships", verbose_name="用户",
    )
    role = models.CharField("角色", max_length=20, choices=Role.choices, default=Role.MEMBER)
    added_at = models.DateTimeField("添加时间", auto_now_add=True)

    class Meta:
        verbose_name = "项目成员"
        verbose_name_plural = verbose_name
        unique_together = [("project", "user")]
