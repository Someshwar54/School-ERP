# Backend guide (FastAPI)

## Layout

```
backend/
├── app/
│   ├── main.py                 app factory: logging, error handlers, security headers, mounts /api/v1
│   ├── core/                   framework-level plumbing (no business rules)
│   │   ├── config.py           typed settings; loads env/<APP_ENV>.env + .env; production guards
│   │   ├── db.py               engine/session; tenant context re-applied at every transaction start
│   │   ├── errors.py           AppError + handlers producing the single error envelope
│   │   ├── security.py         Argon2id hashing, opaque tokens, constant-time compare
│   │   ├── logging.py          JSON logs with per-request id
│   │   └── rate_limit.py       in-process limiter for low-volume public endpoints
│   ├── api/
│   │   ├── deps.py             tenant resolution, session auth, CSRF, account/permission dependencies
│   │   ├── responses.py        OpenAPI docs for the error envelope
│   │   └── v1/
│   │       ├── __init__.py     api_router: the list of domain routers
│   │       └── routes/         one module per domain: auth, public, shared, student, teacher, staff,
│   │                           hr, finance, management
│   ├── schemas/                pydantic request/response models per domain + validated school settings
│   ├── services/               business rules, one module per domain (see below)
│   ├── models/                 SQLAlchemy models (58 tables)
│   ├── seed/                   idempotent fictional demo data (local only)
│   └── tools/                  developer tools (OpenAPI export)
├── env/                        per-environment config: development.env, test.env, e2e.env, production.env.example
├── migrations/                 Alembic: 0001 schema, 0002 row-level security + append-only triggers
└── tests/                      pytest: auth, access control, workflows, tenancy/schema, architecture guards
```

### Services by domain

| Module | Responsibility |
|---|---|
| `auth`, `auth_context`, `rbac`, `workspace` | Sign-in, sessions, permissions catalogue, server-computed menus |
| `school`, `school_config`, `lookups` | School settings/calendar, configuration updates, shared batched lookups |
| `teaching` | Assignment checks every teacher operation goes through |
| `attendance`, `academics`, `lessons` | Registers + corrections, assessments/marks/publication, topic progression |
| `student_portal`, `teacher_portal` | Read models composed for the student and teacher screens |
| `staff_self_service`, `hr`, `documents` | Own attendance/leave/duties, directory/approvals/payroll, document metadata |
| `finance` | Ledger-derived balances and payment recording |
| `announcements`, `messaging`, `complaints`, `feedback` | Communication features with audience/assignment rules |
| `analytics`, `evaluations`, `admissions`, `audit` | Management aggregates, teacher evaluation, enquiries, audit trail |

## Request lifecycle

1. `get_tenant` resolves the school from the trusted hostname table and sets `app.school_id` for RLS.
2. `get_auth` loads the session (by token hash, under RLS), enforces expiry/idle timeout, CSRF and
   Origin on unsafe methods, and builds an `AuthContext` (user, school, permissions, profile ids).
3. Route dependencies (`student_ctx`, `teacher_ctx`, `require_permission(...)`, `management_permission(...)`)
   reject the wrong account type or missing permission with 403.
4. The route calls **one** service function with the `AuthContext` and a validated schema.
5. The service applies business rules (assignment checks, state transitions), writes data and an audit
   event in the same transaction, and commits.
6. Errors raised anywhere become the standard envelope (see `core/errors.py`): `AppError` → its status;
   validation → 422; `IntegrityError` → 409 `conflict`; database unavailable → 503; anything else → 500.

## Adding an endpoint (checklist)

1. **Schema** — add the request model to `app/schemas/<domain>.py` (`<Thing>Create/Update`).
2. **Service** — add `verb_noun(ctx, body)` to `app/services/<domain>.py`: check access (e.g.
   `teaching.assert_teaches`), validate state, write, `audit.record(...)`, `db.commit()`. Raise `AppError`.
3. **Route** — add a thin function to `app/api/v1/routes/<domain>.py` using the right dependency.
   A new domain gets a new routes module, listed in `app/api/v1/__init__.py`.
4. **Permission** — if new, add it to `services/rbac.py` and the relevant role templates (re-run the seed).
5. **Tables** — new model in `app/models/`, then `alembic revision --autogenerate`, review it, and add the
   table to an RLS migration (the structure test fails until you do).
6. **Tests** — happy path + the authorisation boundary (who must be refused).
7. **Docs** — `python -m app.tools.export_openapi`.

## Configuration

`APP_ENV` selects `env/<APP_ENV>.env` (committed, non-secret defaults). `backend/.env` (git-ignored)
holds personal overrides; real environment variables win over both. Production values come from the
hosting platform's secrets; `Settings` refuses to start production with demo/unsafe values.
