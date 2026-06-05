# ── 迭代模型 ─────────────────────────────────────────────────────
from django.db import models
from django.utils import timezone
import uuid


class Iteration(models.Model):
    """迭代周期"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE,
        related_name="iterations", verbose_name="项目",
    )
    name = models.CharField("名称", max_length=200)
    description = models.TextField("描述", blank=True, default="")
    start_date = models.DateField("开始日期")
    end_date = models.DateField("结束日期")
    is_active = models.BooleanField("进行中", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "迭代"
        verbose_name_plural = verbose_name
        ordering = ["-start_date"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gt=models.F("start_date")),
                name="end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.project.identifier}/{self.name}"

    @property
    def task_count(self):
        return self.tasks.count()

    @property
    def completed_count(self):
        return self.tasks.filter(status__type="completed").count()
