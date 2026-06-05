from django.urls import path
from .views import project_statistics

urlpatterns = [
    path("", project_statistics, name="project-statistics"),
]
