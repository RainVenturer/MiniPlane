# ── WebSocket Consumer ────────────────────────────────────────────
"""
通知实时推送 — 用户登录后连接 ws://host/ws/notifications/?token=<jwt>
服务端将实时通知推送到对应用户频道
"""
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from apps.core.websocket import get_user_from_token, get_query_param


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """个人通知 WebSocket — 用户专属频道 user_{id}"""

    async def connect(self):
        token = get_query_param(self.scope, "token")
        if not token:
            await self.close(code=4001)
            return

        self.user = await get_user_from_token(token)
        if not self.user:
            await self.close(code=4001)
            return

        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        """接收来自 channel layer 的通知消息并推送到前端"""
        await self.send_json(event["notification"])

    async def receive_json(self, content, **kwargs):
        """接收前端消息（如标记已读）"""
        action = content.get("action")
        if action == "mark_read":
            from apps.notifications.models import Notification
            from channels.db import database_sync_to_async

            @database_sync_to_async
            def mark_read(notif_id):
                Notification.objects.filter(
                    id=notif_id, recipient=self.user,
                ).update(is_read=True)

            notif_id = content.get("notification_id")
            if notif_id:
                await mark_read(notif_id)
                await self.send_json({"action": "marked_read", "notification_id": notif_id})
