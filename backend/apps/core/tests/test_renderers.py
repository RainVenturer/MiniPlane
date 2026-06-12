"""
core 模块 — 渲染器单元测试

测试覆盖:
  - APIRenderer: 成功响应包装
  - APIRenderer: 分页数据特殊处理
  - APIRenderer: 4xx 响应不包装
"""

import json
import pytest
from unittest.mock import Mock, patch
from apps.core.renderers import APIRenderer


class TestAPIRenderer:
    """APIRenderer — 统一响应格式"""

    def test_wraps_success_response(self):
        renderer = APIRenderer()
        renderer_context = {"response": Mock(status_code=200)}
        result_json = renderer.render(
            {"name": "test"},
            renderer_context=renderer_context,
        )
        result = json.loads(result_json)
        assert result["success"] is True
        assert result["data"] == {"name": "test"}
        assert result["message"] == ""

    def test_wraps_none_data_as_empty_dict(self):
        renderer = APIRenderer()
        renderer_context = {"response": Mock(status_code=200)}
        result_json = renderer.render(None, renderer_context=renderer_context)
        result = json.loads(result_json)
        assert result["success"] is True
        assert result["data"] == {}

    def test_skips_error_responses(self):
        """4xx 响应不包装（由 exception_handler 处理）"""
        renderer = APIRenderer()
        error_data = {"success": False, "message": "错误", "errors": {}}
        renderer_context = {"response": Mock(status_code=400)}
        result_json = renderer.render(error_data, renderer_context=renderer_context)
        result = json.loads(result_json)
        assert result == error_data  # 不修改错误响应

    def test_handles_paginated_response(self):
        """分页数据提取 results 到 data，添加 pagination"""
        renderer = APIRenderer()
        renderer_context = {"response": Mock(status_code=200)}
        paginated_data = {
            "results": [{"id": 1}, {"id": 2}],
            "page": 1,
            "page_size": 20,
            "count": 50,
        }
        result_json = renderer.render(paginated_data, renderer_context=renderer_context)
        result = json.loads(result_json)
        assert result["success"] is True
        assert result["data"] == [{"id": 1}, {"id": 2}]
        assert result["pagination"] == {"page": 1, "page_size": 20, "total": 50}

    def test_no_renderer_context_graceful(self):
        """无 renderer_context 也不崩溃"""
        renderer = APIRenderer()
        result_json = renderer.render({"key": "val"})
        result = json.loads(result_json)
        assert result["success"] is True
        assert result["data"] == {"key": "val"}
