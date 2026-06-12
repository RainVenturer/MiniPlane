"""
core 模块 — 异常处理单元测试

测试覆盖:
  - custom_exception_handler: 统一错误格式
  - _get_first_error: 提取第一条错误信息
"""

import pytest
from unittest.mock import Mock, patch
from rest_framework.views import exception_handler
from apps.core.exceptions import custom_exception_handler, _get_first_error


class TestGetFirstError:
    """_get_first_error"""

    def test_field_error(self):
        errors = {"email": ["请输入有效的邮箱地址"]}
        result = _get_first_error(errors)
        assert result == "email: 请输入有效的邮箱地址"

    def test_non_field_error(self):
        errors = {"non_field_errors": ["全局错误"]}
        result = _get_first_error(errors)
        assert result == "全局错误"

    def test_string_value(self):
        errors = {"email": "无效邮箱"}
        result = _get_first_error(errors)
        assert result == "无效邮箱"

    def test_empty_errors(self):
        result = _get_first_error({})
        assert result == "请求处理失败"

    def test_multiple_errors_takes_first(self):
        errors = {
            "email": ["邮箱无效"],
            "password": ["密码太短"],
        }
        result = _get_first_error(errors)
        assert result == "email: 邮箱无效"


class TestCustomExceptionHandler:
    """custom_exception_handler"""

    def test_formats_validation_error(self):
        """DRF 校验错误 → {success, message, errors}"""
        # 模拟 DRF exception_handler 返回的 response
        mock_response = Mock(status_code=400)
        mock_response.data = {
            "email": ["请输入有效的邮箱地址"],
            "password": ["该字段是必填项"],
        }
        with patch("apps.core.exceptions.exception_handler", return_value=mock_response):
            exc = Exception("test")
            response = custom_exception_handler(exc, {})
            assert response is not None
            assert response.data["success"] is False
            assert "email" in response.data["message"]
            assert "email" in response.data["errors"]

    def test_handles_list_data(self):
        """list 类型的错误数据 → non_field_errors"""
        mock_response = Mock(status_code=400)
        mock_response.data = ["全局校验失败"]
        with patch("apps.core.exceptions.exception_handler", return_value=mock_response):
            response = custom_exception_handler(Exception(), {})
            assert response.data["errors"]["non_field_errors"] == ["全局校验失败"]

    def test_returns_none_for_no_response(self):
        """exception_handler 返回 None 时保持不变"""
        with patch("apps.core.exceptions.exception_handler", return_value=None):
            response = custom_exception_handler(Exception(), {})
            assert response is None

    def test_formats_string_error(self):
        """单个 string 错误"""
        mock_response = Mock(status_code=400)
        mock_response.data = {"detail": "未找到"}
        with patch("apps.core.exceptions.exception_handler", return_value=mock_response):
            response = custom_exception_handler(Exception(), {})
            assert response.data["success"] is False
            assert response.data["errors"]["detail"] == ["未找到"]

    def test_preserves_status_code(self):
        """保持原始 HTTP 状态码"""
        mock_response = Mock(status_code=403)
        mock_response.data = {"detail": "无权限"}
        with patch("apps.core.exceptions.exception_handler", return_value=mock_response):
            response = custom_exception_handler(Exception(), {})
            assert response.status_code == 403
