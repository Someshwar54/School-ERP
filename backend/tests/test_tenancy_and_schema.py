"""Multi-tenant isolation (API, RLS, composite FKs), migrations, seed idempotency and append-only audit."""

import uuid

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.core.db import get_engine, session_factory
from app.models import AuditEvent, Enrollment, Section, StudentProfile, User
from app.seed.demo import seed
from tests.conftest import HOST_B, ApiClient, alembic_config, as_user, student_phone, tenant_session


def test_school_b_student_cannot_sign_in_at_school_a() -> None:
    phone_b = student_phone("STU0001", "school-b")
    assert phone_b != student_phone("STU0001")
    # The same Student ID exists in both schools; credentials only work at the school that issued them.
    ApiClient().login("student", "STU0001", phone_b, expect=401)
    b = ApiClient(HOST_B)
    b.login("student", "STU0001", phone_b)
    assert b.get("/auth/me").json()["school"]["slug"] == "school-b"


def test_session_from_one_school_is_rejected_at_another() -> None:
    a = as_user("staff", "EMP1001")
    token = a.http.cookies.get("erp_session")
    b = ApiClient(HOST_B)
    b.http.cookies.set("erp_session", token)
    assert b.get("/auth/me").status_code == 401
    assert b.get("/teacher/dashboard").status_code == 401


def test_unknown_host_is_rejected_without_fallback() -> None:
    r = ApiClient("unknown.example").http.post(
        "/api/v1/auth/login", json={"portal": "student", "login_id": "STU0001", "password": "x"}
    )
    assert r.status_code == 404 and r.json()["error"]["code"] == "unknown_school"


def test_school_b_data_never_appears_in_school_a_views() -> None:
    overview = as_user("director", "DIR001").get("/management/overview").json()
    assert overview["kpis"]["enrolled_students"] == 300  # school B has 3 students, not counted
    b_teacher = as_user("staff", "EMP1001", host=HOST_B)
    assert len(b_teacher.get("/teacher/assignments").json()) >= 1
    assert all(a["section"] == "6-A" for a in b_teacher.get("/teacher/assignments").json())
    assert as_user("director", "DIR001", host=HOST_B).get("/management/overview").json()["kpis"]["enrolled_students"] == 3


def test_row_level_security_hides_other_tenants_rows() -> None:
    s = tenant_session("demo")
    try:
        assert s.scalar(select(func.count()).select_from(StudentProfile)) == 300
    finally:
        s.close()
    s = tenant_session("school-b")
    try:
        assert s.scalar(select(func.count()).select_from(StudentProfile)) == 3
    finally:
        s.close()
    raw = session_factory()()
    try:
        assert raw.scalar(select(func.count()).select_from(User)) == 0  # no tenant set: default deny
    finally:
        raw.close()


def test_rls_blocks_writing_rows_for_another_tenant() -> None:
    s_b = tenant_session("school-b")
    b_id = s_b.info["school_id"]
    s_b.close()
    s = tenant_session("demo")
    try:
        s.add(AuditEvent(school_id=uuid.UUID(b_id), action="attack", details={}))
        with pytest.raises(DBAPIError):
            s.flush()
    finally:
        s.rollback()
        s.close()


def test_composite_foreign_keys_reject_cross_school_references() -> None:
    s_b = tenant_session("school-b")
    section_b = s_b.scalar(select(Section.id))
    s_b.close()
    s = tenant_session("demo")
    try:
        student_a = s.scalar(select(StudentProfile).where(StudentProfile.student_code == "STU0300"))
        year_a = s.scalar(select(Enrollment.academic_year_id).limit(1))
        s.add(
            Enrollment(
                school_id=student_a.school_id, student_id=student_a.id, section_id=section_b, academic_year_id=year_a, roll_no=99
            )
        )
        with pytest.raises(IntegrityError):
            s.flush()
    finally:
        s.rollback()
        s.close()


def test_audit_log_is_append_only() -> None:
    s = tenant_session("demo")
    try:
        with pytest.raises(DBAPIError):
            s.execute(text("UPDATE audit_events SET action = 'tampered'"))
    finally:
        s.rollback()
        s.close()
    s = tenant_session("demo")
    try:
        with pytest.raises(DBAPIError):
            s.execute(text("DELETE FROM audit_events"))
    finally:
        s.rollback()
        s.close()


def test_migrations_are_at_head() -> None:
    head = ScriptDirectory.from_config(alembic_config()).get_current_head()
    with get_engine().connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == head


def test_app_role_is_not_superuser_and_cannot_bypass_rls() -> None:
    with get_engine().connect() as conn:
        row = conn.execute(text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")).one()
    assert row == (False, False)


def test_demo_seed_is_idempotent() -> None:
    tables = ["users", "student_profiles", "attendance_records", "marks", "invoices", "payments", "lesson_topics"]

    def counts() -> dict[str, int]:
        s = tenant_session("demo")
        try:
            return {t: s.execute(text(f"SELECT count(*) FROM {t}")).scalar() for t in tables}
        finally:
            s.close()

    before = counts()
    seed()
    assert counts() == before


def test_seed_refuses_production(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import config

    settings = config.get_settings()
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(SystemExit):
        seed()


def test_health_endpoints() -> None:
    c = ApiClient()
    assert c.http.get("/api/v1/health").json() == {"status": "ok"}
    assert c.http.get("/api/v1/health/ready").json()["status"] == "ready"
