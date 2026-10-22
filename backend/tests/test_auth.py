import pytest
from sqlalchemy import select

from app.core.config import Settings, get_settings
from tests.conftest import ApiClient, as_user, student_phone, tenant_session

GENERIC = "The ID or password is incorrect."


def test_student_login_resolves_only_own_account() -> None:
    c = as_user("student", "STU0181")
    me = c.get("/auth/me").json()
    assert me["user"]["login_id"] == "STU0181"
    assert me["workspace"]["kind"] == "student"
    profile = c.get("/student/profile").json()
    assert profile["student_code"] == "STU0181"
    # The phone number (initial demo password) is never returned in full.
    assert student_phone("STU0181") not in str(profile)
    assert profile["phone_masked"].endswith(student_phone("STU0181")[-4:])


def test_login_is_case_insensitive_for_ids() -> None:
    c = ApiClient()
    c.login("student", "stu0182", student_phone("STU0182"))


def test_session_cookie_is_httponly_and_csrf_cookie_is_readable(client: ApiClient) -> None:
    r = client.login("staff", "EMP1002", "Staff@1002")
    cookies = r.headers.get_list("set-cookie")
    session = next(c for c in cookies if c.startswith("erp_session="))
    csrf = next(c for c in cookies if c.startswith("erp_csrf="))
    assert "HttpOnly" in session and "SameSite=lax" in session
    assert "HttpOnly" not in csrf


@pytest.mark.parametrize(
    ("portal", "login_id", "password"),
    [
        ("student", "STU0183", "wrong-password"),  # wrong password
        ("student", "STU9999", "anything"),  # unknown account
        ("staff", "STU0183", "__PHONE__"),  # right password, wrong portal
        ("director", "EMP1001", "Staff@1001"),  # staff cannot use the Director portal
        ("director", "DIR009", "Mgmt@DIR009"),  # management account without a management role
        ("student", "DIR001", "Mgmt@DIR001"),
    ],
)
def test_failed_logins_are_generic(client: ApiClient, portal: str, login_id: str, password: str) -> None:
    if password == "__PHONE__":
        password = student_phone("STU0183")
    r = client.login(portal, login_id, password, expect=401)
    assert r.json()["error"]["message"] == GENERIC
    assert "erp_session" not in r.cookies


def test_invalid_login_payload_is_validated(client: ApiClient) -> None:
    r = client.http.post("/api/v1/auth/login", json={"portal": "admin", "login_id": "x' OR 1=1", "password": ""})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_rate_limit_after_repeated_failures(client: ApiClient) -> None:
    for _ in range(5):
        client.login("student", "STU0290", "nope", expect=401)
    r = client.login("student", "STU0290", student_phone("STU0290"), expect=429)
    assert r.json()["error"]["code"] == "rate_limited"


def test_protected_endpoints_require_a_session(client: ApiClient) -> None:
    for path in ["/auth/me", "/student/dashboard", "/teacher/dashboard", "/management/overview", "/hr/payroll"]:
        r = client.get(path)
        assert r.status_code == 401, path


def test_state_changes_require_csrf_token() -> None:
    c = as_user("staff", "EMP2005")
    body = {"leave_type": "casual", "starts_on": "2099-01-01", "ends_on": "2099-01-01", "reason": "Test"}
    assert c.post("/staff/leave", body, csrf=False).status_code == 403
    assert c.post("/staff/leave", body, headers={"X-CSRF-Token": "forged"}, csrf=False).status_code == 403
    assert c.post("/staff/leave", body, headers={"Origin": "https://evil.example"}).status_code == 403


def test_logout_revokes_session() -> None:
    c = as_user("staff", "EMP1003")
    assert c.post("/auth/logout").status_code == 200
    c.http.cookies.clear()
    assert c.get("/auth/me").status_code == 401


def test_logout_revokes_token_server_side() -> None:
    c = as_user("staff", "EMP1005")
    token = c.http.cookies.get("erp_session")
    c.post("/auth/logout")
    replay = ApiClient()
    replay.http.cookies.set("erp_session", token)
    assert replay.get("/auth/me").status_code == 401


def test_change_password_rules_and_session_revocation() -> None:
    phone = student_phone("STU0250")
    first, second = as_user("student", "STU0250"), as_user("student", "STU0250")
    weak = first.post("/auth/change-password", {"current_password": phone, "new_password": "short"})
    assert weak.status_code == 400
    uses_phone = first.post("/auth/change-password", {"current_password": phone, "new_password": f"x{phone}abc"})
    assert uses_phone.status_code == 400
    wrong_current = first.post("/auth/change-password", {"current_password": "nope", "new_password": "BetterPass2026"})
    assert wrong_current.status_code == 400
    ok = first.post("/auth/change-password", {"current_password": phone, "new_password": "BetterPass2026"})
    assert ok.status_code == 200 and ok.json()["other_sessions_signed_out"] >= 1
    assert second.get("/auth/me").status_code == 401  # other session revoked
    assert first.get("/auth/me").json()["user"]["must_change_password"] is False
    ApiClient().login("student", "STU0250", phone, expect=401)  # old password no longer works
    ApiClient().login("student", "STU0250", "BetterPass2026")


def test_enforced_password_change_blocks_other_endpoints() -> None:
    settings = get_settings()
    settings.enforce_password_change = True
    try:
        c = as_user("student", "STU0251")
        assert c.get("/auth/me").status_code == 200
        r = c.get("/student/dashboard")
        assert r.status_code == 403 and r.json()["error"]["code"] == "password_change_required"
    finally:
        settings.enforce_password_change = False


def test_passwords_are_hashed_never_plaintext() -> None:
    from app.models import User

    s = tenant_session("demo")
    try:
        user = s.scalar(select(User).where(User.login_id == "STU0181"))
        assert user is not None
        assert user.password_hash.startswith("$argon2id$")
        assert student_phone("STU0181") not in user.password_hash
    finally:
        s.close()


def test_production_configuration_rejects_demo_settings() -> None:
    with pytest.raises(ValueError, match="Unsafe production configuration"):
        Settings(app_env="production", database_url="postgresql+psycopg://u:p@h/db")
