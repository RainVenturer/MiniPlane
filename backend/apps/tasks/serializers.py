# ── 任务序列化器 ─────────────────────────────────────────────────
from rest_framework import serializers
from django.db import transaction
from .models import Task, TaskStatus


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ["id", "project", "name", "color", "order", "type"]
        read_only_fields = ["id"]


class TaskListSerializer(serializers.ModelSerializer):
    """任务列表（轻量）"""
    status_name = serializers.CharField(source="status.name", read_only=True)
    status_color = serializers.CharField(source="status.color", read_only=True)
    assignee_name = serializers.CharField(source="assignee.name", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "title", "priority", "priority_display", "status",
            "status_name", "status_color", "assignee", "assignee_name",
            "due_date", "order", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    """任务详情"""
    status_name = serializers.CharField(source="status.name", read_only=True)
    status_color = serializers.CharField(source="status.color", read_only=True)
    status_type = serializers.CharField(source="status.type", read_only=True)
    assignee_name = serializers.CharField(source="assignee.name", read_only=True)
    module_name = serializers.CharField(source="module.name", read_only=True)
    iteration_name = serializers.CharField(source="iteration.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.name", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    subtask_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "project", "parent", "title", "description", "priority",
            "priority_display", "status", "status_name", "status_color", "status_type",
            "assignee", "assignee_name", "module", "module_name",
            "iteration", "iteration_name", "due_date", "start_date",
            "order", "created_by", "created_by_name", "subtask_count",
            "comment_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "project", "created_by", "created_at", "updated_at"]

    @staticmethod
    def get_subtask_count(obj):
        return obj.subtasks.count()

    @staticmethod
    def get_comment_count(obj):
        return obj.comments.count()


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "title", "description", "priority", "status", "assignee",
            "module", "iteration", "due_date", "start_date", "parent",
        ]
        extra_kwargs = {
            "status": {"required": False},
            "parent": {"required": False},
        }

    def create(self, validated_data):
        validated_data["project_id"] = self.context["project_id"]
        validated_data["created_by"] = self.context["request"].user
        # 未指定状态时，取项目的第一个未开始状态
        if "status" not in validated_data:
            validated_data["status"] = TaskStatus.objects.filter(
                project_id=self.context["project_id"],
                type=TaskStatus.Type.UNSTARTED,
            ).first()
            if not validated_data["status"]:
                validated_data["status"] = TaskStatus.objects.filter(
                    project_id=self.context["project_id"],
                ).first()
        return super().create(validated_data)


class TaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "title", "description", "priority", "status", "assignee",
            "module", "iteration", "due_date", "start_date", "order",
        ]


class TaskStatusChangeSerializer(serializers.Serializer):
    """状态变更"""
    status = serializers.UUIDField()

    def validate_status(self, value):
        task = self.context["task"]
        if not TaskStatus.objects.filter(id=value, project=task.project).exists():
            raise serializers.ValidationError("目标状态不属于当前项目")
        return value

    @transaction.atomic
    def save(self):
        task = self.context["task"]
        old_status = task.status
        new_status = TaskStatus.objects.get(id=self.validated_data["status"])
        task.status = new_status
        task.save(update_fields=["status", "updated_at"])
        # 记录操作日志
        from apps.activities.models import Activity
        Activity.objects.create(
            task=task, project=task.project,
            actor=self.context["request"].user,
            action="status_changed", field="status",
            old_value=str(old_status.id), new_value=str(new_status.id),
        )
        # 发送通知
        from apps.notifications.services import notify_task_status_changed
        notify_task_status_changed(task, old_status.name, new_status.name,
                                    self.context["request"].user)
        return task
