# ── 模块模型 ─────────────────────────────────────────────────────
from django.db import models
from django.conf import settings
import uuid


class Module(models.Model):
    """项目模块"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE,
        related_name="modules", verbose_name="项目",
    )
    name = models.CharField("名称", max_length=200)
    description = models.TextField("描述", blank=True, default="")
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="led_modules", verbose_name="负责人",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "模块"
        verbose_name_plural = verbose_name
        unique_together = [("project", "name")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.project.identifier}/{self.name}"
