# ── 评论序列化器 ─────────────────────────────────────────────────
from rest_framework import serializers
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.name", read_only=True)
    author_avatar = serializers.CharField(source="author.avatar", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "task", "author", "author_name", "author_avatar",
                   "content", "created_at", "updated_at"]
        read_only_fields = ["id", "task", "author", "created_at", "updated_at"]


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["content"]

    def create(self, validated_data):
        validated_data["task_id"] = self.context["task_id"]
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)
