# ── 通知信号 ─────────────────────────────────────────────────────
"""
Django Signals — 自动响应业务事件创建通知
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.tasks.models import Task
from .services import notify_task_assigned


@receiver(post_save, sender=Task)
def on_task_created_or_assigned(sender, instance, created, raw, **kwargs):
    """任务创建或被更新时，若负责人变更则通知"""
    if raw:
        return
    if created and instance.assignee:
        # 任务创建时通知负责人
        # 避免在已有显式调用的地方重复触发
        pass
