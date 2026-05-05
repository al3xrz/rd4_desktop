from __future__ import annotations

import pytest

from tests.test_models_smoke import configure_temp_database


def test_ensure_initial_admin_creates_login_user_once(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.services.auth import AuthService
    from app.services.bootstrap import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME, ensure_initial_admin

    assert ensure_initial_admin() is True
    assert ensure_initial_admin() is False

    user = AuthService().login(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)
    assert user.username == DEFAULT_ADMIN_USERNAME
    assert user.role.value == "admin"


def test_auth_service_admin_user_management(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.models import Role
    from app.services.auth import AuthService
    from app.services.exceptions import PermissionDeniedError

    auth = AuthService()
    admin = auth.create_user({"username": "admin", "password": "secret", "role": Role.ADMIN})
    operator = auth.create_user({"username": "operator", "password": "secret", "role": Role.OPERATOR}, admin)

    assert len(auth.list_users(admin)) == 2

    auth.update_user(operator.id, {"name": "Operator", "role": Role.CASHIER}, admin)
    auth.reset_password(operator.id, "new-secret", admin)
    assert auth.login("operator", "new-secret").role == Role.CASHIER

    auth.set_user_active(operator.id, False, admin)
    try:
        auth.login("operator", "new-secret")
    except PermissionDeniedError:
        pass
    else:
        raise AssertionError("blocked user should not log in")

    with pytest.raises(PermissionDeniedError):
        auth.list_users(operator)
