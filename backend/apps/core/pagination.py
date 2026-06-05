# ── 标准分页器 ──────────────────────────────────────────────────
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """标准分页：?page=1&page_size=20"""
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response({
            "results": data,
            "page": self.page.number,
            "page_size": self.get_page_size(self.request),
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
        })
