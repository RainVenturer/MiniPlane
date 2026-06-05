# ── 操作日志模型 ─────────────────────────────────────────────────
from django.db import models
from django.conf import settings
import uuid


class Activity(models.Model):
    """关键操作日志 — 追溯任务/项目变更"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        "tasks.Task", on_delete=models.CASCADE,
        null=True, blank=True, related_name="activities", verbose_name="任务",
    )
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE,
        related_name="activities", verbose_name="项目",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="activities", verbose_name="操作者",
    )
    action = models.CharField("操作类型", max_length=50)
    field = models.CharField("变更字段", max_length=100, blank=True, default="")
    old_value = models.TextField("旧值", blank=True, default="")
    new_value = models.TextField("新值", blank=True, default="")
    created_at = models.DateTimeField("操作时间", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["task", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.actor} {self.action} — {self.created_at}"
