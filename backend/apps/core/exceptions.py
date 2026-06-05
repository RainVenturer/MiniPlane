# ── 全局异常处理 ────────────────────────────────────────────────
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """统一错误响应为 {success, message, errors} 格式"""
    response = exception_handler(exc, context)

    if response is not None:
        errors = {}
        if isinstance(response.data, dict):
            for field, msgs in response.data.items():
                errors[field] = msgs if isinstance(msgs, list) else [str(msgs)]
        elif isinstance(response.data, list):
            errors["non_field_errors"] = response.data

        response.data = {
            "success": False,
            "message": _get_first_error(errors),
            "errors": errors,
        }

    return response


def _get_first_error(errors: dict) -> str:
    """提取第一条错误信息"""
    for field, msgs in errors.items():
        if isinstance(msgs, list) and msgs:
            msg = msgs[0]
            return str(msg) if field == "non_field_errors" else f"{field}: {msg}"
        elif isinstance(msgs, str):
            return msgs
    return "请求处理失败"
