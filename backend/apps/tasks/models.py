# ── 任务模型 ─────────────────────────────────────────────────────
from django.db import models
from django.conf import settings
import uuid


class TaskStatus(models.Model):
    """任务状态列 — 每项目可自定义"""
    class Type(models.TextChoices):
        BACKLOG = "backlog", "待办"
        UNSTARTED = "unstarted", "未开始"
        STARTED = "started", "进行中"
        COMPLETED = "completed", "已完成"
        CANCELLED = "cancelled", "已取消"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE,
        related_name="task_statuses", verbose_name="项目",
    )
    name = models.CharField("名称", max_length=50)
    color = models.CharField("颜色", max_length=7, default="#6366f1")
    order = models.PositiveIntegerField("排序", default=0)
    type = models.CharField("类型", max_length=20, choices=Type.choices, default=Type.UNSTARTED)

    class Meta:
        verbose_name = "任务状态"
        verbose_name_plural = verbose_name
        ordering = ["order"]
        unique_together = [("project", "name")]

    def __str__(self):
        return f"{self.project.identifier}/{self.name}"


class Task(models.Model):
    """任务"""
    class Priority(models.TextChoices):
        URGENT = "urgent", "紧急"
        HIGH = "high", "高"
        MEDIUM = "medium", "中"
        LOW = "low", "低"
        NONE = "none", "无"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE,
        related_name="tasks", verbose_name="项目",
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True,
        related_name="subtasks", verbose_name="父任务",
    )
    status = models.ForeignKey(
        TaskStatus, on_delete=models.PROTECT,
        related_name="tasks", verbose_name="状态",
    )
    title = models.CharField("标题", max_length=300)
    description = models.TextField("描述", blank=True, default="")
    priority = models.CharField(
        "优先级", max_length=10,
        choices=Priority.choices, default=Priority.NONE,
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="assigned_tasks", verbose_name="负责人",
    )
    module = models.ForeignKey(
        "modules.Module", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="tasks", verbose_name="模块",
    )
    iteration = models.ForeignKey(
        "iterations.Iteration", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="tasks", verbose_name="迭代",
    )
    due_date = models.DateField("截止日期", null=True, blank=True)
    start_date = models.DateField("开始日期", null=True, blank=True)
    order = models.FloatField("排序", default=0.0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="created_tasks", verbose_name="创建者",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = verbose_name
        ordering = ["order", "-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "assignee"]),
            models.Index(fields=["project", "priority"]),
            models.Index(fields=["project", "iteration"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"[{self.project.identifier}] {self.title}"
