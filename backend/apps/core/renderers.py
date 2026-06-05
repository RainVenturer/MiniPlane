# ── 统一 API 渲染器 ─────────────────────────────────────────────
from rest_framework.renderers import JSONRenderer


class APIRenderer(JSONRenderer):
    """统一包装成功响应为 {success, data, message} 格式"""
    media_type = "application/json"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # 跳过非标准响应（如 drf-spectacular 的 schema）
        response = renderer_context.get("response") if renderer_context else None
        if response and response.status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)

        wrapped = {
            "success": True,
            "data": data if data is not None else {},
            "message": "",
        }

        # 分页数据特殊处理
        if isinstance(data, dict) and "results" in data:
            pagination = {
                "page": data.get("page", 1),
                "page_size": data.get("page_size", 20),
                "total": data.get("count", 0),
            }
            wrapped["data"] = data["results"]
            wrapped["pagination"] = pagination

        return super().render(wrapped, accepted_media_type, renderer_context)
