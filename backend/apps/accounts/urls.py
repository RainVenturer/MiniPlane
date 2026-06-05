from django.urls import path
from .views import AuthViewSet

urlpatterns = [
    path("register/", AuthViewSet.as_view({"post": "register"}), name="auth-register"),
    path("login/", AuthViewSet.as_view({"post": "login"}), name="auth-login"),
    path("logout/", AuthViewSet.as_view({"post": "logout"}), name="auth-logout"),
    path("me/", AuthViewSet.as_view({"get": "me", "put": "update_me"}), name="auth-me"),
    path("change-password/", AuthViewSet.as_view({"post": "change_password"}), name="auth-change-password"),
]
