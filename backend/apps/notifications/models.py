# ── 通知模型 ─────────────────────────────────────────────────────
from django.db import models
from django.conf import settings
import uuid


class Notification(models.Model):
    """系统通知"""
    class Type(models.TextChoices):
        TASK_ASSIGNED = "task.assigned", "任务分配"
        TASK_COMMENTED = "task.commented", "任务评论"
        TASK_STATUS_CHANGED = "task.status_changed", "状态变更"
        MEMBER_ADDED = "member.added", "成员加入"
        MENTION = "mention", "@提及"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notifications", verbose_name="接收者",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="sent_notifications", verbose_name="触发者",
    )
    type = models.CharField("类型", max_length=50, choices=Type.choices)
    message = models.TextField("消息内容")
    reference_type = models.CharField("关联类型", max_length=50, blank=True)
    reference_id = models.UUIDField("关联ID", null=True, blank=True)
    is_read = models.BooleanField("已读", default=False, db_index=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "通知"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "-created_at"]),
        ]

    def __str__(self):
        return f"[{self.get_type_display()}] {self.message[:50]}"
