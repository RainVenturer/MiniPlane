# ── 操作日志序列化器 ─────────────────────────────────────────────
from rest_framework import serializers
from .models import Activity


class ActivitySerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.name", read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True)

    class Meta:
        model = Activity
        fields = ["id", "task", "task_title", "project", "actor", "actor_name",
                   "action", "field", "old_value", "new_value", "created_at"]
        read_only_fields = ["id", "created_at"]
