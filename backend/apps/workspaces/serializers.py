# ── 工作空间序列化器 ─────────────────────────────────────────────
from rest_framework import serializers
from .models import Workspace, WorkspaceMember


class WorkspaceSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.name", read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ["id", "name", "slug", "description", "owner", "owner_name",
                   "member_count", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "slug", "created_at", "updated_at"]

    @staticmethod
    def get_member_count(obj):
        return obj.members.count()


class WorkspaceCreateSerializer(WorkspaceSerializer):
    class Meta(WorkspaceSerializer.Meta):
        fields = ["name", "description"]

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        # 自动生成 slug
        name = validated_data["name"]
        slug = self._make_slug(name)
        validated_data["slug"] = slug
        return super().create(validated_data)

    @staticmethod
    def _make_slug(name: str) -> str:
        """生成唯一 slug"""
        import re
        base = re.sub(r"[^\w\-]", "-", name.lower()).strip("-")[:100]
        slug = base or "workspace"
        # 确保唯一
        from .models import Workspace
        if not Workspace.objects.filter(slug=slug).exists():
            return slug
        for i in range(1, 100):
            candidate = f"{base}-{i}"
            if not Workspace.objects.filter(slug=candidate).exists():
                return candidate
        import uuid
        return f"{base}-{uuid.uuid4().hex[:6]}"


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ["id", "user", "user_name", "user_email", "role", "joined_at"]
        read_only_fields = ["id", "joined_at"]


class AddMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=WorkspaceMember.Role.choices, default="member")


class ChangeRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=WorkspaceMember.Role.choices)
