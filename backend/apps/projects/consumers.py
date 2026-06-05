# ── 项目 WebSocket Consumer ──────────────────────────────────────
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from apps.core.websocket import get_user_from_token, get_query_param


class ProjectConsumer(AsyncJsonWebsocketConsumer):
    """项目实时协作频道 — 订阅 project_{id}"""

    async def connect(self):
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        token = get_query_param(self.scope, "token")
        if not token:
            await self.close(code=4001)
            return

        self.user = await get_user_from_token(token)
        if not self.user:
            await self.close(code=4001)
            return

        # 校验用户是否属于该项目
        from channels.db import database_sync_to_async
        is_member = await database_sync_to_async(
            lambda: self.user.project_memberships.filter(
                project_id=self.project_id,
            ).exists()
        )()
        if not is_member:
            await self.close(code=4003)
            return

        self.group_name = f"project_{self.project_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def project_event(self, event):
        """接收项目事件（任务状态变更等）并推送到前端"""
        await self.send_json(event["data"])

    async def receive_json(self, content, **kwargs):
        """接收前端消息（如看板拖动同步）"""
        action = content.get("action")
        if action == "task_moved":
            # 广播给项目内其他成员
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "project_event",
                    "data": {
                        "action": "task_moved",
                        "task_id": content.get("task_id"),
                        "status_id": content.get("status_id"),
                        "actor": {"id": str(self.user.id), "name": self.user.name},
                    },
                },
            )
