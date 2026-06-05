# ── 通知服务 ─────────────────────────────────────────────────────
"""
通知发送服务 — 被其他模块调用，同时触发 DB 存储 + WebSocket 推送
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification


def _create_and_send(recipient, actor, type_, message, ref_type="", ref_id=None):
    """创建通知记录并推送 WebSocket"""
    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        type=type_,
        message=message,
        reference_type=ref_type,
        reference_id=ref_id,
    )
    # 通过 WebSocket 实时推送
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"user_{recipient.id}",
            {
                "type": "send_notification",
                "notification": {
                    "id": str(notification.id),
                    "type": notification.type,
                    "message": notification.message,
                    "actor": {"id": str(actor.id), "name": actor.name},
                    "reference_type": notification.reference_type,
                    "reference_id": str(notification.reference_id) if notification.reference_id else None,
                    "is_read": False,
                    "created_at": notification.created_at.isoformat(),
                },
            },
        )
    return notification


def notify_task_assigned(task, actor):
    """任务被分配"""
    if task.assignee and task.assignee != actor:
        _create_and_send(
            recipient=task.assignee,
            actor=actor,
            type_=Notification.Type.TASK_ASSIGNED,
            message=f"{actor.name} 将任务「{task.title}」分配给你",
            ref_type="task",
            ref_id=task.id,
        )


def notify_task_commented(task, comment, actor):
    """任务被评论"""
    if task.assignee and task.assignee != actor:
        _create_and_send(
            recipient=task.assignee,
            actor=actor,
            type_=Notification.Type.TASK_COMMENTED,
            message=f"{actor.name} 评论了任务「{task.title}」",
            ref_type="task",
            ref_id=task.id,
        )


def notify_task_status_changed(task, old_status_name, new_status_name, actor):
    """任务状态变更"""
    if task.assignee and task.assignee != actor:
        _create_and_send(
            recipient=task.assignee,
            actor=actor,
            type_=Notification.Type.TASK_STATUS_CHANGED,
            message=f"{actor.name} 将任务「{task.title}」从「{old_status_name}」变更为「{new_status_name}」",
            ref_type="task",
            ref_id=task.id,
        )
