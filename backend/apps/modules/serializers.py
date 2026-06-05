# ── 模块序列化器 ─────────────────────────────────────────────────
from rest_framework import serializers
from .models import Module


class ModuleSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source="lead.name", read_only=True)
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ["id", "project", "name", "description", "lead",
                   "lead_name", "task_count", "created_at", "updated_at"]
        read_only_fields = ["id", "project", "created_at", "updated_at"]

    @staticmethod
    def get_task_count(obj):
        return obj.tasks.count()


class ModuleCreateSerializer(ModuleSerializer):
    class Meta(ModuleSerializer.Meta):
        fields = ["name", "description", "lead"]

    def create(self, validated_data):
        validated_data["project_id"] = self.context["project_id"]
        return super().create(validated_data)
