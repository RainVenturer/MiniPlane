# ── 迭代序列化器 ─────────────────────────────────────────────────
from rest_framework import serializers
from .models import Iteration


class IterationSerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField(read_only=True)
    completed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Iteration
        fields = ["id", "project", "name", "description", "start_date",
                   "end_date", "is_active", "task_count", "completed_count",
                   "created_at", "updated_at"]
        read_only_fields = ["id", "project", "created_at", "updated_at"]


class IterationCreateSerializer(IterationSerializer):
    class Meta(IterationSerializer.Meta):
        fields = ["name", "description", "start_date", "end_date"]

    def validate(self, attrs):
        if attrs["end_date"] <= attrs["start_date"]:
            raise serializers.ValidationError({"end_date": "结束日期必须晚于开始日期"})
        return attrs

    def create(self, validated_data):
        validated_data["project_id"] = self.context["project_id"]
        return super().create(validated_data)


class AddTasksToIterationSerializer(serializers.Serializer):
    task_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
    )
