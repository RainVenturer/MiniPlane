# ── 用户认证视图 ─────────────────────────────────────────────────
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    UserSerializer,
)


@extend_schema_view(
    register=extend_schema(summary="用户注册", tags=["认证"]),
    login=extend_schema(summary="用户登录", tags=["认证"]),
    logout=extend_schema(summary="退出登录", tags=["认证"]),
    me=extend_schema(summary="获取当前用户信息", tags=["认证"]),
    update_me=extend_schema(summary="更新个人信息", tags=["认证"]),
    change_password=extend_schema(summary="修改密码", tags=["认证"]),
)
class AuthViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ("register", "login"):
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(methods=["post"], detail=False)
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = self._get_tokens(user)
        return Response({
            "user": UserSerializer(user).data,
            "access": tokens["access"],
            "refresh": tokens["refresh"],
        }, status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=False)
    def login(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = self._get_tokens(user)
        return Response({
            "user": UserSerializer(user).data,
            "access": tokens["access"],
            "refresh": tokens["refresh"],
        })

    @action(methods=["post"], detail=False)
    def logout(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({"detail": "已退出登录"})

    @action(methods=["get"], detail=False)
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(methods=["put"], detail=False, url_path="me")
    def update_me(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=["post"], detail=False, url_path="change-password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "密码修改成功"})

    @staticmethod
    def _get_tokens(user) -> dict:
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
