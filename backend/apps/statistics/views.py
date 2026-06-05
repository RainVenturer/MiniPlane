# ── 统计视图 ─────────────────────────────────────────────────────
"""
项目统计 + 迭代统计 API
"""
from django.db.models import Count, Q, OuterRef, Subquery
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.projects.models import Project
from apps.iterations.models import Iteration
from apps.tasks.models import Task, TaskStatus


@extend_schema(summary="项目统计", tags=["统计"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def project_statistics(request, pk):
    """项目任务统计 — 总览数据"""
    project = get_object_or_404(Project, id=pk)

    # 总任务数
    total = Task.objects.filter(project=project).count()

    # 各状态分布
    status_distribution = (
        Task.objects.filter(project=project, parent__isnull=True)
        .values("status__name", "status__color", "status__type")
        .annotate(count=Count("id"))
        .order_by("status__order")
    )

    # 各优先级分布
    priority_distribution = (
        Task.objects.filter(project=project, parent__isnull=True)
        .values("priority")
        .annotate(count=Count("id"))
    )

    # 各负责人分布
    assignee_distribution = (
        Task.objects.filter(project=project, parent__isnull=True)
        .values("assignee__name", "assignee__id")
        .annotate(count=Count("id"))
        .exclude(assignee__isnull=True)
    )

    # 逾期任务数
    overdue = Task.objects.filter(
        project=project,
        due_date__lt=timezone.now().date(),
        status__type__in=["unstarted", "started"],
    ).count()

    # 已完成数
    completed = Task.objects.filter(
        project=project, status__type="completed",
    ).count()

    return Response({
        "total_tasks": total,
        "completed_tasks": completed,
        "overdue_tasks": overdue,
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
        "status_distribution": list(status_distribution),
        "priority_distribution": list(priority_distribution),
        "assignee_distribution": list(assignee_distribution),
    })


@extend_schema(summary="迭代统计", tags=["统计"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def iteration_statistics(request, pk):
    """迭代统计 — 燃尽图数据"""
    iteration = get_object_or_404(Iteration, id=pk)

    tasks = Task.objects.filter(iteration=iteration, parent__isnull=True)
    total = tasks.count()
    completed = tasks.filter(status__type="completed").count()
    overdue = tasks.filter(
        due_date__lt=timezone.now().date(),
    ).exclude(status__type="completed").count()

    # 各状态分布
    by_status = (
        tasks.values("status__name", "status__color")
        .annotate(count=Count("id"))
        .order_by("status__order")
    )

    # 按负责人
    by_assignee = (
        tasks.values("assignee__name", "assignee__id")
        .annotate(count=Count("id"))
        .exclude(assignee__isnull=True)
    )

    return Response({
        "iteration": {
            "id": str(iteration.id),
            "name": iteration.name,
            "start_date": iteration.start_date,
            "end_date": iteration.end_date,
        },
        "total_tasks": total,
        "completed_tasks": completed,
        "overdue_tasks": overdue,
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
        "by_status": list(by_status),
        "by_assignee": list(by_assignee),
    })
