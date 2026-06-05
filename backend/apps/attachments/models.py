# ── 附件模型 ─────────────────────────────────────────────────────
from django.db import models
from django.conf import settings
import uuid


def attachment_upload_path(instance, filename):
    """存储路径: attachments/{task_id}/{uuid}_{filename}"""
    ext = filename.split(".")[-1] if "." in filename else ""
    return f"attachments/{instance.task_id}/{uuid.uuid4().hex}.{ext}"


class Attachment(models.Model):
    """任务附件 — 存入 MinIO/S3"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        "tasks.Task", on_delete=models.CASCADE,
        related_name="attachments", verbose_name="任务",
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="attachments", verbose_name="上传者",
    )
    file = models.FileField("文件", upload_to=attachment_upload_path)
    filename = models.CharField("文件名", max_length=255)
    size = models.PositiveIntegerField("文件大小(字节)", default=0)
    mime_type = models.CharField("MIME类型", max_length=100, blank=True)
    created_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        verbose_name = "附件"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.filename} ({self.size} bytes)"
