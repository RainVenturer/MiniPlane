# ── 通知序列化器 ─────────────────────────────────────────────────
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.name", read_only=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "type", "type_display", "message", "actor",
                   "actor_name", "reference_type", "reference_id",
                   "is_read", "created_at"]
        read_only_fields = ["id", "created_at"]
