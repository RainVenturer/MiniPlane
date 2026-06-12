# ── 项目序列化器 ─────────────────────────────────────────────────
from rest_framework import serializers
from .models import Project, ProjectMember


class ProjectSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source="lead.name", read_only=True)
    member_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ["id", "workspace", "name", "identifier", "description",
                   "lead", "lead_name", "is_archived", "member_count",
                   "task_count", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    @staticmethod
    def get_member_count(obj):
        return obj.members.count()

    @staticmethod
    def get_task_count(obj):
        return obj.tasks.count()


class ProjectCreateSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        fields = ["name", "identifier", "description", "lead"]

    def validate_identifier(self, value):
        if not value.isalnum():
            raise serializers.ValidationError("标识符只能包含字母和数字")
        value = value.upper()
        workspace_id = self.context.get("workspace_id")
        if workspace_id and Project.objects.filter(
            workspace_id=workspace_id, identifier=value,
        ).exists():
            raise serializers.ValidationError("该项目标识符在当前工作空间中已存在")
        return value

    def create(self, validated_data):
        validated_data["workspace_id"] = self.context["workspace_id"]
        return super().create(validated_data)


class ProjectMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = ProjectMember
        fields = ["id", "user", "user_name", "user_email", "role", "added_at"]
        read_only_fields = ["id", "added_at"]


class AddProjectMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=ProjectMember.Role.choices, default="member")
