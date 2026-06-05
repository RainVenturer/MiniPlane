from django.urls import path, include
from .views import WorkspaceViewSet
from apps.projects.views import ProjectViewSet

# 嵌套在工作空间下的项目路由
project_list = ProjectViewSet.as_view({"get": "list", "post": "create"})

urlpatterns = [
    path("", WorkspaceViewSet.as_view({"get": "list", "post": "create"}), name="workspace-list"),
    path("<uuid:pk>/", WorkspaceViewSet.as_view({
        "get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy",
    }), name="workspace-detail"),
    path("<uuid:pk>/members/", WorkspaceViewSet.as_view({
        "get": "members", "post": "members",
    }), name="workspace-members"),
    path("<uuid:pk>/members/<uuid:uid>/", WorkspaceViewSet.as_view({
        "put": "change_role", "delete": "remove_member",
    }), name="workspace-member-detail"),
    path("<uuid:ws_id>/projects/", project_list, name="workspace-project-list"),
]
