"""Test harness: a dedicated PostgreSQL test database, migrated from scratch and seeded.

School A ("demo", host localhost) is the full demo dataset. School B ("school-b", host
school-b.test) is a minimal second tenant used to attack tenant isolation.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://school_app:school_app_dev_password@localhost:5432/school_erp_test")
os.environ["APP_ENV"] = "test"
os.environ["PASSWORD_HASH_PROFILE"] = "fast-test"
os.environ["LOGIN_MAX_FAILURES_PER_IP"] = "10000"
os.environ["TENANT_FALLBACK_TO_DEFAULT"] = "false"

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import session_factory, set_tenant
from app.main import app
from app.models import School, StudentProfile
from app.seed.demo import SeedOptions, seed

HOST_A, HOST_B = "localhost", "school-b.test"


def alembic_config() -> Config:
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "migrations"))
    cfg.attributes["skip_logging"] = True
    return cfg


@pytest.fixture(scope="session", autouse=True)
def database() -> Iterator[None]:
    cfg = alembic_config()
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    seed()
    seed(
        SeedOptions(
            slug="school-b",
            name="Second Demo School",
            hosts=(HOST_B,),
            grades=(6,),
            sections_per_grade=1,
            students_per_section=3,
            full=False,
        )
    )
    yield


@pytest.fixture
def db() -> Iterator[Session]:
    s = session_factory()()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


def tenant_session(slug: str) -> Session:
    s = session_factory()()
    school = s.scalar(select(School).where(School.slug == slug))
    assert school is not None
    set_tenant(s, school.id)
    return s


def student_phone(code: str, slug: str = "demo") -> str:
    s = tenant_session(slug)
    try:
        phone = s.scalar(select(StudentProfile.phone).where(StudentProfile.student_code == code))
        assert phone
        return phone
    finally:
        s.close()


class ApiClient:
    """TestClient wrapper that remembers the CSRF token after login, like the browser client does."""

    def __init__(self, host: str = HOST_A) -> None:
        self.http = TestClient(app, base_url=f"http://{host}")
        self.csrf: str | None = None

    def login(self, portal: str, login_id: str, password: str, expect: int = 200):  # type: ignore[no-untyped-def]
        r = self.http.post("/api/v1/auth/login", json={"portal": portal, "login_id": login_id, "password": password})
        assert r.status_code == expect, r.text
        if r.status_code == 200:
            self.csrf = r.cookies.get("erp_csrf") or self.http.cookies.get("erp_csrf")
        return r

    def get(self, path: str, **kw):  # type: ignore[no-untyped-def]
        return self.http.get(f"/api/v1{path}", **kw)

    def _send(self, method: str, path: str, json: object | None = None, csrf: bool = True, **kw):  # type: ignore[no-untyped-def]
        headers = kw.pop("headers", {})
        if csrf and self.csrf:
            headers["X-CSRF-Token"] = self.csrf
        return self.http.request(method, f"/api/v1{path}", json=json, headers=headers, **kw)

    def post(self, path: str, json: object | None = None, **kw):  # type: ignore[no-untyped-def]
        return self._send("POST", path, json, **kw)

    def put(self, path: str, json: object | None = None, **kw):  # type: ignore[no-untyped-def]
        return self._send("PUT", path, json, **kw)

    def patch(self, path: str, json: object | None = None, **kw):  # type: ignore[no-untyped-def]
        return self._send("PATCH", path, json, **kw)


def as_user(portal: str, login_id: str, password: str | None = None, host: str = HOST_A) -> ApiClient:
    c = ApiClient(host)
    if password is None:
        if portal == "student":
            password = student_phone(login_id, "demo" if host == HOST_A else "school-b")
        elif portal == "staff":
            password = f"Staff@{login_id[-4:]}"
        else:
            password = f"Mgmt@{login_id}"
    c.login(portal, login_id, password)
    return c


@pytest.fixture
def client() -> ApiClient:
    return ApiClient()
