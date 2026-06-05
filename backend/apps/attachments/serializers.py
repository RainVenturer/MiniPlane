# ── 附件序列化器 ─────────────────────────────────────────────────
from rest_framework import serializers
from django.conf import settings
from .models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    uploader_name = serializers.CharField(source="uploader.name", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ["id", "task", "file", "filename", "size", "mime_type",
                   "uploader", "uploader_name", "file_url", "created_at"]
        read_only_fields = ["id", "task", "uploader", "filename", "size",
                             "mime_type", "created_at"]

    @staticmethod
    def get_file_url(obj):
        if obj.file:
            return obj.file.url
        return None


class AttachmentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["file"]

    def validate_file(self, value):
        max_size = getattr(settings, "FILE_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError(f"文件大小不能超过 {max_size // (1024*1024)}MB")
        return value

    def create(self, validated_data):
        validated_data["task_id"] = self.context["task_id"]
        validated_data["uploader"] = self.context["request"].user
        validated_data["filename"] = validated_data["file"].name
        validated_data["size"] = validated_data["file"].size
        validated_data["mime_type"] = validated_data["file"].content_type or ""
        return super().create(validated_data)
