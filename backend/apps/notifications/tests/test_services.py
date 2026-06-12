"""
notifications 模块 — Service 层单元测试

测试覆盖:
  - _create_and_send: 创建通知 + WebSocket 推送
  - notify_task_assigned: 跳过自己/创建通知
  - notify_task_commented: 跳过自己/跳过无 assignee
  - notify_task_status_changed
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

pytestmark = pytest.mark.django_db


class TestCreateAndSend:
    """_create_and_send 核心函数"""

    @patch("apps.notifications.services.async_to_sync")
    @patch("apps.notifications.services.get_channel_layer")
    def test_creates_notification_and_pushes_ws(
        self, mock_get_channel, mock_async_to_sync, admin_user, extra_user,
    ):
        """创建 DB 通知并推送 WebSocket"""
        mock_channel = MagicMock()
        mock_get_channel.return_value = mock_channel
        mock_async_to_sync.return_value = lambda *a, **kw: None

        from apps.notifications.services import _create_and_send
        from apps.notifications.models import Notification

        notification = _create_and_send(
            recipient=extra_user,
            actor=admin_user,
            type_=Notification.Type.TASK_ASSIGNED,
            message="Test notification",
            ref_type="task",
            ref_id=None,
        )

        assert notification.recipient == extra_user
        assert notification.actor == admin_user
        assert notification.type == Notification.Type.TASK_ASSIGNED
        assert notification.message == "Test notification"

        # async_to_sync 被调用（WebSocket 推送）
        mock_async_to_sync.assert_called_once()

    @patch("apps.notifications.services.get_channel_layer", return_value=None)
    def test_no_channel_layer_graceful(self, mock_get_channel, admin_user, extra_user):
        """channel layer 不可用时不崩溃"""
        from apps.notifications.services import _create_and_send
        from apps.notifications.models import Notification

        notification = _create_and_send(
            recipient=extra_user,
            actor=admin_user,
            type_=Notification.Type.TASK_ASSIGNED,
            message="No WS",
        )
        assert notification.recipient == extra_user


class TestNotifyTaskAssigned:
    """notify_task_assigned"""

    @patch("apps.notifications.services._create_and_send")
    def test_notifies_when_assignee_different(self, mock_create_send, admin_user, extra_user):
        """分配者 != 被分配者 — 发送通知"""
        from apps.notifications.services import notify_task_assigned
        task = Mock(assignee=extra_user, title="Test Task", id="task-id")
        notify_task_assigned(task, admin_user)
        mock_create_send.assert_called_once()
        call_kwargs = mock_create_send.call_args[1]
        assert call_kwargs["recipient"] == extra_user
        assert call_kwargs["actor"] == admin_user
        assert "分配给你" in call_kwargs["message"]

    @patch("apps.notifications.services._create_and_send")
    def test_skips_self_assignment(self, mock_create_send, admin_user):
        """自己分配给自己 — 不发送通知"""
        from apps.notifications.services import notify_task_assigned
        task = Mock(assignee=admin_user, title="My Task", id="task-id")
        notify_task_assigned(task, admin_user)
        mock_create_send.assert_not_called()

    @patch("apps.notifications.services._create_and_send")
    def test_skips_when_no_assignee(self, mock_create_send, admin_user):
        """无 assignee — 不发送通知"""
        from apps.notifications.services import notify_task_assigned
        task = Mock(assignee=None, title="Unassigned", id="task-id")
        notify_task_assigned(task, admin_user)
        mock_create_send.assert_not_called()


class TestNotifyTaskCommented:
    """notify_task_commented"""

    @patch("apps.notifications.services._create_and_send")
    def test_notifies_assignee(self, mock_create_send, admin_user, extra_user):
        """评论者 != assignee — 发送通知"""
        from apps.notifications.services import notify_task_commented
        task = Mock(assignee=extra_user, title="Task")
        comment = Mock()
        notify_task_commented(task, comment, admin_user)
        mock_create_send.assert_called_once()
        assert "评论了任务" in mock_create_send.call_args[1]["message"]

    @patch("apps.notifications.services._create_and_send")
    def test_skips_own_task_comment(self, mock_create_send, admin_user):
        """评论自己分配的任务 — 不通知"""
        from apps.notifications.services import notify_task_commented
        task = Mock(assignee=admin_user, title="My Task")
        comment = Mock()
        notify_task_commented(task, comment, admin_user)
        mock_create_send.assert_not_called()

    @patch("apps.notifications.services._create_and_send")
    def test_skips_if_no_assignee(self, mock_create_send, admin_user):
        """无 assignee 时不通知"""
        from apps.notifications.services import notify_task_commented
        task = Mock(assignee=None, title="Unassigned")
        comment = Mock()
        notify_task_commented(task, comment, admin_user)
        mock_create_send.assert_not_called()


class TestNotifyTaskStatusChanged:
    """notify_task_status_changed"""

    @patch("apps.notifications.services._create_and_send")
    def test_notifies_assignee(self, mock_create_send, admin_user, extra_user):
        """状态变更 — 通知 assignee"""
        from apps.notifications.services import notify_task_status_changed
        task = Mock(assignee=extra_user, title="Task")
        notify_task_status_changed(task, "待办", "进行中", admin_user)
        mock_create_send.assert_called_once()
        assert "待办" in mock_create_send.call_args[1]["message"]
        assert "进行中" in mock_create_send.call_args[1]["message"]

    @patch("apps.notifications.services._create_and_send")
    def test_skips_self_status_change(self, mock_create_send, admin_user):
        """自己改自己任务状态 — 不通知"""
        from apps.notifications.services import notify_task_status_changed
        task = Mock(assignee=admin_user, title="My Task")
        notify_task_status_changed(task, "待办", "进行中", admin_user)
        mock_create_send.assert_not_called()
