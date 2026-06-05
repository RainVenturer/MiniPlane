# ── User 模型 ────────────────────────────────────────────────────
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    """用邮箱作为唯一标识"""

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("邮箱地址为必填项")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class User(AbstractUser):
    """MiniPlane 用户 — 邮箱登录"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, blank=True, default="")
    email = models.EmailField("邮箱地址", unique=True, db_index=True)
    name = models.CharField("姓名", max_length=100, blank=True)
    avatar = models.URLField("头像", blank=True, default="")
    created_at = models.DateTimeField("注册时间", default=timezone.now, editable=False)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name or self.email} ({self.email})"
