# ── 任务筛选器 ───────────────────────────────────────────────────
import django_filters
from django.db import models
from .models import Task


class TaskFilter(django_filters.FilterSet):
    """支持多条件组合筛选"""
    status = django_filters.UUIDFilter(field_name="status_id")
    assignee = django_filters.UUIDFilter(field_name="assignee_id")
    priority = django_filters.ChoiceFilter(choices=Task.Priority.choices)
    iteration = django_filters.UUIDFilter(field_name="iteration_id")
    module = django_filters.UUIDFilter(field_name="module_id")
    due_date_before = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")
    due_date_after = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")
    search = django_filters.CharFilter(method="filter_search", label="关键词搜索")
    parent__isnull = django_filters.BooleanFilter(field_name="parent", lookup_expr="isnull",
                                                   label="只看顶层任务")

    class Meta:
        model = Task
        fields = [
            "status", "assignee", "priority", "iteration", "module",
            "due_date_before", "due_date_after", "search", "parent__isnull",
        ]

    @staticmethod
    def filter_search(queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(description__icontains=value)
        )
