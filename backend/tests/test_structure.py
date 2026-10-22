"""Guards that keep the architecture from eroding as features are added."""

import ast
from pathlib import Path

from sqlalchemy import text

from app.core.db import get_engine
from app.main import app
from app.models import GLOBAL_TABLES, Base

APP_DIR = Path(__file__).resolve().parents[1] / "app"


def test_every_tenant_table_has_row_level_security() -> None:
    tenant_tables = {t.name for t in Base.metadata.sorted_tables if "school_id" in t.c and t.name not in GLOBAL_TABLES}
    with get_engine().connect() as conn:
        protected = set(
            conn.execute(
                text("SELECT relname FROM pg_class WHERE relrowsecurity AND relforcerowsecurity AND relkind = 'r'")
            ).scalars()
        )
    missing = tenant_tables - protected
    assert not missing, f"Add these tables to an RLS migration: {sorted(missing)}"


def test_services_do_not_depend_on_the_http_layer() -> None:
    offenders = []
    for path in (APP_DIR / "services").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(("app.api", "fastapi")):
                offenders.append(f"{path.name}: {node.module}")
    assert not offenders, offenders


def test_request_schemas_live_in_app_schemas() -> None:
    offenders = []
    files = [*(APP_DIR / "services").rglob("*.py"), *(p for p in (APP_DIR / "api").rglob("*.py") if p.name != "responses.py")]
    for path in files:
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ClassDef) and any(getattr(b, "id", "") == "BaseModel" for b in node.bases):
                offenders.append(f"{path.relative_to(APP_DIR)}: {node.name}")
    assert not offenders, offenders


def test_every_api_route_is_versioned_and_documents_errors() -> None:
    schema = app.openapi()
    assert "ErrorEnvelope" in schema["components"]["schemas"]
    for path, ops in schema["paths"].items():
        assert path.startswith("/api/v1/"), path
        for method, op in ops.items():
            assert "422" in op["responses"], f"{method.upper()} {path} has no documented error responses"
            assert op.get("tags"), f"{method.upper()} {path} has no tag"
