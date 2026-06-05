"""
Celery 异步任务配置
"""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("miniplane")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
