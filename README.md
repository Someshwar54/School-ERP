# School Website + School ERP (prototype)

A school-specific public website connected to a role-aware School ERP, built for one **fictional** school
(*Sunrise Valley Public School*) on a foundation designed for multi-school SaaS.

> **Prototype status.** Core flows work end to end against PostgreSQL and are covered by automated tests.
> All people, numbers and content are fictional. This is **not** production-ready — see
> [Known limitations](#known-limitations-and-security-work-before-production).

| Layer | Technology (versions verified together) |
|---|---|
| Frontend | Next.js 16.4 (App Router, Turbopack, Cache Components), React 19.3, TypeScript (strict), Tailwind CSS 4, lucide-react, zod 4, Plotly.js 4 (lazy-loaded) |
| Backend | Python 3.13, FastAPI 0.159, SQLAlchemy 2.1, Alembic 1.20, psycopg 3.3, pydantic 2.14, argon2-cffi 25 |
| Database | PostgreSQL 16 with row-level security |
| Tests | pytest 9, Playwright 1.64, ruff, mypy, ESLint 9, `tsc` |

## Project structure

```
school-platform/
├── backend/                     FastAPI + PostgreSQL            → docs/BACKEND.md
│   ├── app/api/v1/routes/       thin HTTP routers, one per domain (auth, public, shared, student, teacher,
│   │                            staff, hr, finance, management) mounted at /api/v1
│   ├── app/api/deps.py          tenant resolution, session auth, CSRF, account/permission dependencies
│   ├── app/services/            business rules, one module per domain (no FastAPI imports)
│   ├── app/schemas/             request/response models + validated school settings
│   ├── app/models/              58 SQLAlchemy tables
│   ├── app/core/                config, db + tenant context, errors, security, logging, rate limiting
│   ├── app/seed/ · app/tools/   fictional demo seed · OpenAPI/endpoint-doc export
│   ├── env/                     per-environment config (development, test, e2e, production example)
│   ├── migrations/              0001 schema · 0002 row-level security + append-only triggers
│   └── tests/                   pytest (auth, access control, workflows, tenancy, architecture guards)
├── frontend/                    Next.js                          → docs/FRONTEND.md
│   ├── src/app/                 routes only (metadata + one-line pages), error/404 boundaries
│   ├── src/features/            screens by area: site, auth, workspace, common, student, teacher, staff, management
│   ├── src/services/            typed API layer (the only place that knows endpoint URLs)
│   ├── src/domain/              pure business rules (validation, attendance, status) + unit tests
│   ├── src/components/          ui primitives (barrel export) and charts
│   ├── src/lib/ · hooks/ · providers/   API client + TanStack Query hooks, generic hooks, app providers
│   ├── src/config/              validated env + white-label school config
│   └── e2e/                     Playwright tests (desktop + mobile)
├── scripts/                     setup_db.sh, e2e_backend.sh
├── docs/                        ARCHITECTURE, BACKEND, FRONTEND, API, CONVENTIONS, API_ENDPOINTS (generated)
└── CLAUDE.md                    rules + commands for AI-assisted changes
```

## Run it locally

Prerequisites: Python 3.12+, Node 20.9+, PostgreSQL 16 running locally.

```bash
# 1. Databases (creates role school_app NOSUPERUSER NOBYPASSRLS, and school_erp / _test / _e2e)
./scripts/setup_db.sh

# 2. Backend
cd backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt
                                          # config: env/development.env (optional overrides: .env)
./.venv/bin/alembic upgrade head          # apply migrations
./.venv/bin/python -m app.seed.demo       # fictional demo data (safe to re-run; ~30 s first time)
./.venv/bin/uvicorn app.main:app --reload --port 8000
#   API docs: http://localhost:8000/api/docs   Health: /api/v1/health, /api/v1/health/ready

# 3. Frontend (new terminal)
cd frontend
npm install
                                          # config: .env.development (optional overrides: .env.local)
npm run dev                               # http://localhost:3000
```

### Database and migrations

* Migrations: `alembic upgrade head` / `alembic downgrade base` (both directions are exercised by the test suite).
* New migration after model changes: `alembic revision --autogenerate -m "..."`, then review it. Add any new
  tenant table to the RLS list in a follow-up migration.
* The app must connect as a **non-superuser** role; superusers bypass row-level security.

### Demo seed

`python -m app.seed.demo` creates one school with Grades 6–10 (2 sections each), 300 students, 14 teachers,
6 non-teaching staff, 9 management accounts, timetable, ~90 school days of attendance, 4 assessments per
subject (3 published, 1 unpublished/partly entered), lesson topics, fees/payments/refund, announcements,
events, complaints, feedback, messages, leave, duties and an evaluation rubric. It matches on natural keys,
never duplicates rows, never resets passwords, and **refuses to run when `APP_ENV=production`**.

## Demo login accounts (local development only)

All accounts are fictional and start with `must_change_password = true`. Print the full list, including
each demo student's initial password, with:

```bash
cd backend && ./.venv/bin/python -m app.seed.show_demo_accounts
```

| Portal | ID | Password | What it demonstrates |
|---|---|---|---|
| Student | `STU0181` (Shreya Chopra, 9-A) | her seeded phone number — `9246989102` on a fresh seed | Student workspace |
| Student | `STU0001`–`STU0300` | each student's seeded phone (see command above) | Prototype convention: Student ID + phone |
| Staff | `EMP1001` | `Staff@1001` | Maths teacher **and** class teacher of 9-A (one account, both workspaces) |
| Staff | `EMP1002` | `Staff@1002` | Subject teacher only (no class-teacher workspace) |
| Staff | `EMP1004` | `Staff@1004` | Class teacher of 9-B, which has a missing register to fill in |
| Staff | `EMP2001` | `Staff@2001` | Finance staff: fees module, can record payments |
| Staff | `EMP2002` | `Staff@2002` | HR staff: directory + leave list, cannot approve, no payroll |
| Staff | `EMP2003` / `EMP2004` | `Staff@2003` / `Staff@2004` | Librarian / transport (module marked *planned*) |
| Staff | `EMP2005` | `Staff@2005` | Ordinary non-teaching staff: self-service only |
| Director | `DIR001` | `Mgmt@DIR001` | Director (broad access incl. payroll, confidential complaints) |
| Director | `DIR002` | `Mgmt@DIR002` | Principal (confidential complaints, publish results, no payroll) |
| Director | `DIR003` | `Mgmt@DIR003` | Board member (aggregates only) |
| Director | `DIR004`–`DIR007` | `Mgmt@<ID>` | Finance manager, HR manager, academic coordinator, owner |
| Director | `DIR008` | `Mgmt@DIR008` | Technical administrator (configuration + audit only) |
| Director | `DIR009` | `Mgmt@DIR009` | Management account with **no role** — sign-in is refused |

These credentials exist only in the local seed and this README; none are in frontend source code.

## Implemented and tested

**Public website** — home, about, academics, admissions, facilities, faculty (approved public fields only),
news & events, contact with validated admission-enquiry form (stored; email/SMS clearly marked not connected),
responsive header with mobile menu and a prominent top-right **ERP Portal** button, accessible forms, skip link,
focus styles, reduced-motion support. Branding from a typed, validated config.

**ERP entry and authentication** — portal page with exactly Student / Staff / Director login; three distinct
sign-in pages (ID, password, show/hide, validation, loading and error states, honest recovery page); Argon2id
hashing; server-side sessions in HttpOnly cookies; CSRF tokens + Origin checks; absolute and idle expiry;
logout; sign out other sessions; DB-backed rate limiting; generic failures; portal-to-account-type checks;
password change with policy (rejects ID/phone) that revokes other sessions; optional enforced password change.

**Student workspace (14 sections)** — dashboard, profile (phone masked; guardians with verification status),
attendance calendar with all statuses / holidays / not-recorded days and monthly trend, academic performance,
published results only, timetable, fees ledger (invoices, concessions, payments, refunds, derived balance),
announcements, events, documents + printable report card generated from published results, teacher messaging
(assigned teachers only), complaints (confidential routing), topic-understanding feedback and anonymous feedback,
account settings.

**Teacher workspace** — dashboard with pending tasks, timetable, assigned classes, attendance (daily register for
class teachers, per-period for timetabled teachers; correction reasons + history; holiday/future/window checks),
assessments and marks (validation, absent handling, published-correction reasons + history), lesson progression
(start / continue / keep pending / confirmed completion / reopen with reason; dismissing never completes),
topic feedback and student messages, assigned complaints, class-teacher overview (attendance × subjects,
follow-up list, missing records).

**Non-teaching staff** — role-configured menu: own attendance, leave requests (overlap checks, cancel), duties,
documents, profile; finance and HR modules only with permission; library/transport shown honestly as planned.

**Management portal** — executive overview (KPIs, action items, recent audit activity) with Plotly charts
(attendance trend, subject averages, score distribution, fee collection, exceptions) each with a table view;
academics with publication queue; teacher-evaluation evidence + human-reviewed rubric evaluations; attendance;
fees and finance (record payments, exact decimals, no overpayment); HR directory, leave approvals (no
self-approval) and audited payroll; complaints and aggregated feedback by permission; admission enquiries;
approvals and append-only audit log; validated, versioned school configuration.

**Data and tenancy** — 58-table relational schema with migrations, composite same-school foreign keys, RLS on
all 55 tenant tables, hostname-based tenant resolution, append-only audit/history tables, health checks,
structured JSON logs with request ids, pagination, batched queries.

## Test, lint, type-check and build results (this environment, 22 Oct 2026)

| Check | Command | Result |
|---|---|---|
| Backend tests | `cd backend && .venv/bin/pytest` | **65 passed** (fresh DB: migrate down/up, seed, 2 tenants, architecture guards) |
| Backend lint/format | `ruff check app tests` · `ruff format --check app tests` | passed |
| Backend types | `mypy app` | no issues |
| Frontend checks | `npm run check` (tsc strict, ESLint incl. layer rules, Prettier, vitest) | passed · **11 unit tests** |
| Browser tests | `PLAYWRIGHT_CHROMIUM_PATH=… npm run test:e2e` | **26 passed** (production build, desktop + Pixel 7) |
| Production build | `npm run build` | passed |

Backend tests cover: valid/invalid/unknown/wrong-portal logins, no-role director refused, cookie flags, CSRF and
Origin enforcement, rate limiting, logout/token replay, password change + session revocation, enforced password
change, hashing, production config guard; students blocked from other students' data, staff and management APIs;
teachers blocked from unrelated sections/assessments; subject teacher cannot take daily register; ordinary staff
blocked from finance/HR/management; board member blocked from payroll/invoices/audit/confidential complaints;
technical admin blocked from business data; attendance submission/correction/history; marks validation,
publication gate and corrections; confirmed topic completion; complaint routing; leave segregation; exact-decimal
payments and ledger consistency; cross-school login, cross-school session replay, unknown host, RLS read and
write isolation, composite-FK rejection, append-only audit, non-superuser role, migrations at head, seed
idempotency, seed refusal in production, health checks.

## Not implemented / not connected

* Email, SMS, push notifications; self-service password recovery; MFA (planned for management).
* Online fee payments, payment gateway, bank reconciliation, accounting exports; payslips/payroll runs.
* File storage for documents (metadata only; downloads shown as "not connected").
* Parent/guardian portal (data model ready, see `docs/ARCHITECTURE.md`).
* Library and transport workflows (permission-gated "planned" pages).
* Admin UIs for creating users, classes, timetables, fee structures, announcements (seed/DB only today);
  staff attendance capture (read-only view); report exports and background jobs.
* Public website content is build-time config, not a CMS; custom domains per school need hosting setup.

## Known limitations and security work before production

1. Replace the phone-number initial password with expiring one-time activation codes; enable
   `ENFORCE_PASSWORD_CHANGE`; add verified recovery and **MFA** for management/finance/HR.
2. Deploy behind HTTPS with `COOKIE_SECURE=true`, `__Host-` cookie names, strict `ALLOWED_ORIGINS`, a CSP,
   and `TRUST_PROXY_HEADERS` only when the API is reachable solely via the proxy.
3. The public enquiry limiter is per-process memory; use a shared store (Redis) or WAF with multiple workers.
4. Add an external security review and penetration test; dependency and container scanning in CI.
5. Backups: scheduled `pg_dump`/PITR with encrypted off-site copies and regular restore drills.
6. Observability: ship JSON logs to a central store; add metrics, alerting and error tracking.
7. Data protection: consent, retention and deletion policies (e.g. India's DPDP Act) for student data.
8. Invoice status filtering is done in Python after the query; move derived balances into SQL for large schools.
9. Seed data dates are relative to the day it is run; re-seed a fresh database for demos far in the future.

## Next steps toward a production multi-tenant SaaS

1. **Onboarding & admin**: school provisioning (tenant + domains + role templates), bulk CSV import of students,
   staff and guardians with validation, class/timetable/fee-structure editors, announcement composer.
2. **Identity**: activation codes, MFA, recovery, parent portal with verified child switching, SSO option.
3. **Content per tenant**: move public website content and branding into the backend (per-host), keep build-time
   config as defaults; per-school custom domains with automated TLS.
4. **Jobs & integrations**: a background worker (e.g. RQ/Celery or Postgres-based queue) for notifications,
   report generation and imports with idempotent retries; payment gateway with webhook reconciliation.
5. **Operations**: CI running the same checks as above, staging environment, migrations in deploy pipeline,
   backups/restore drills, monitoring, rate limiting at the edge, load tests per tenant size.
6. **Governance**: per-tenant data export, audit review tooling, retention policies, DPDP compliance review.
