"""
MiniPlane 根 URL 路由
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# 嵌套视图
from apps.tasks.views import TaskViewSet
from apps.comments.views import CommentViewSet
from apps.attachments.views import AttachmentViewSet
from apps.iterations.views import IterationViewSet
from apps.modules.views import ModuleViewSet

urlpatterns = [
    path("admin/", admin.site.urls),

    # API 文档
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # 认证
    path("api/auth/", include("apps.accounts.urls")),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # 工作空间
    path("api/workspaces/", include("apps.workspaces.urls")),

    # 项目 (独立路由)
    path("api/projects/", include("apps.projects.urls")),
    # 项目下嵌套：任务、迭代、模块
    path("api/projects/<uuid:proj_id>/tasks/",
         TaskViewSet.as_view({"get": "list", "post": "create"}), name="project-task-list"),
    path("api/projects/<uuid:proj_id>/task-statuses/",
         TaskViewSet.as_view({"get": "statuses", "post": "statuses"}), name="project-task-statuses"),
    path("api/projects/<uuid:proj_id>/iterations/",
         IterationViewSet.as_view({"get": "list", "post": "create"}), name="project-iteration-list"),
    path("api/projects/<uuid:proj_id>/modules/",
         ModuleViewSet.as_view({"get": "list", "post": "create"}), name="project-module-list"),
    # 项目统计
    path("api/projects/<uuid:pk>/statistics/",
         include("apps.statistics.urls")),

    # 任务 (独立路由 — 详情/编辑/删除)
    path("api/tasks/", include("apps.tasks.urls")),
    # 任务下嵌套：评论、附件
    path("api/tasks/<uuid:task_id>/comments/",
         CommentViewSet.as_view({"get": "list", "post": "create"}), name="task-comment-list"),
    path("api/tasks/<uuid:task_id>/attachments/",
         AttachmentViewSet.as_view({"get": "list", "post": "create"}), name="task-attachment-list"),

    # 评论 (独立路由 — 编辑/删除)
    path("api/comments/", include("apps.comments.urls")),

    # 附件 (独立路由 — 删除)
    path("api/attachments/", include("apps.attachments.urls")),

    # 迭代 (嵌套路由 — 详情/编辑/删除)
    path("api/projects/<uuid:proj_id>/iterations/<uuid:pk>/",
         IterationViewSet.as_view({
             "get": "retrieve", "put": "update",
             "patch": "partial_update", "delete": "destroy",
         }), name="iteration-detail"),
    path("api/projects/<uuid:proj_id>/iterations/<uuid:pk>/tasks/",
         IterationViewSet.as_view({"post": "add_tasks"}),
         name="iteration-add-tasks"),
    # 迭代统计
    path("api/iterations/<uuid:pk>/statistics/",
         include("apps.statistics.iteration_urls")),

    # 模块 (独立路由 — 详情/编辑/删除)
    path("api/modules/", include("apps.modules.urls")),

    # 通知
    path("api/notifications/", include("apps.notifications.urls")),

    # 操作日志 (嵌套在任务/项目下)
    path("api/tasks/<uuid:task_id>/activities/",
         include("apps.activities.task_urls")),
    path("api/projects/<uuid:project_id>/activities/",
         include("apps.activities.project_urls")),
]
