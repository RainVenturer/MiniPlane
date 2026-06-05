# ── WebSocket 工具 ────────────────────────────────────────────────
from urllib.parse import parse_qs
from channels.db import database_sync_to_async


@database_sync_to_async
def get_user_from_token(token: str):
    """从 JWT token 中获取用户"""
    from rest_framework_simplejwt.tokens import AccessToken
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        validated = AccessToken(token)
        user_id = validated.get("user_id")
        return User.objects.get(id=user_id, is_active=True)
    except Exception:
        return None


def get_query_param(scope: dict, key: str) -> str | None:
    """从 WebSocket scope 的查询字符串中提取参数"""
    query_string = scope.get("query_string", b"").decode()
    params = parse_qs(query_string)
    values = params.get(key, [])
    return values[0] if values else None
