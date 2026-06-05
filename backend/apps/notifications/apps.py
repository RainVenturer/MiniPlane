from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "通知"

    def ready(self):
        import apps.notifications.signals  # noqa: 注册信号
