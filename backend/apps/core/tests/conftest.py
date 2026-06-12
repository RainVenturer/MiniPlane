import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com", password="Admin123456", name="Admin"
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="member@test.com", password="Member123456", name="Member"
    )


@pytest.fixture
def extra_user(db):
    return User.objects.create_user(
        email="extra@test.com", password="Extra123456", name="Extra"
    )
