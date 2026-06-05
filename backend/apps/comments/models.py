# ── 评论模型 ─────────────────────────────────────────────────────
from django.db import models
from django.conf import settings
import uuid


class Comment(models.Model):
    """任务评论"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        "tasks.Task", on_delete=models.CASCADE,
        related_name="comments", verbose_name="任务",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="comments", verbose_name="作者",
    )
    content = models.TextField("内容")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = verbose_name
        ordering = ["created_at"]

    def __str__(self):
        return f"评论 {self.id} — {self.author}"
