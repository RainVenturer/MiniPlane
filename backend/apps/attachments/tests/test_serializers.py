"""
attachments 模块 — Serializer 层单元测试

测试覆盖:
  - AttachmentUploadSerializer.validate_file (文件大小限制)
"""

import pytest
from unittest.mock import Mock, patch
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.attachments.serializers import AttachmentUploadSerializer


class TestAttachmentUploadSerializer:
    """AttachmentUploadSerializer 校验"""

    def test_validate_file_within_limit(self):
        """文件大小在限制内"""
        mock_file = Mock(size=5 * 1024 * 1024, name="test.txt")  # 5MB
        serializer = AttachmentUploadSerializer()
        result = serializer.validate_file(mock_file)
        assert result == mock_file

    def test_validate_file_exceeds_limit(self):
        """文件大小超过限制 — 默认 10MB"""
        mock_file = Mock(size=15 * 1024 * 1024, name="large.bin")  # 15MB
        serializer = AttachmentUploadSerializer()
        with pytest.raises(Exception) as exc:
            serializer.validate_file(mock_file)
        assert "文件大小不能超过" in str(exc.value)

    @patch("django.conf.settings.FILE_UPLOAD_MAX_MEMORY_SIZE", 1024)  # 1KB
    def test_validate_file_custom_limit(self):
        """自定义文件大小限制"""
        mock_file = Mock(size=2048, name="big.txt")  # 2KB > 1KB
        serializer = AttachmentUploadSerializer()
        with pytest.raises(Exception) as exc:
            serializer.validate_file(mock_file)
        assert "文件大小不能超过" in str(exc.value)
