from django.urls import path
from .views import iteration_statistics

urlpatterns = [
    path("", iteration_statistics, name="iteration-statistics"),
]
