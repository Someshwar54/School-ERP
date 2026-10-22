# Architecture and design decisions

## Overview

```
Browser ──► Next.js (frontend, :3000)
              │  public website: static pages built from src/config (no private data)
              │  ERP UI: static shells; data fetched client-side from same-origin /api/*
              └─ rewrite /api/* ──► FastAPI (backend, :8000) ──► PostgreSQL 16 (RLS on)
```

* **One modular backend** (`backend/app`): `api/v1/routes` (thin HTTP) → `services/` (business rules,
  no FastAPI) → `models/` (SQLAlchemy); `schemas/` holds request/response models. No microservices.
  Details and the "add an endpoint" checklist: [BACKEND.md](BACKEND.md).
* **Layered frontend** (`frontend/src`): `app/` routes → `features/` screens → `services/` (typed API),
  `domain/` (pure rules), `components/ui` (primitives). Server state in TanStack Query. See [FRONTEND.md](FRONTEND.md).
* Contract and conventions: [API.md](API.md), [CONVENTIONS.md](CONVENTIONS.md).
* **Same-origin API.** The browser only ever talks to the Next.js origin; `/api/*` is proxied to FastAPI.
  This keeps the session cookie first-party (`HttpOnly; SameSite=Lax`) and avoids CORS entirely. The public
  site and ERP can later live on different subdomains/deployments without changing business logic.

## Authentication and sessions

| Decision | Choice | Trade-off |
|---|---|---|
| Credential storage | Argon2id (`argon2-cffi`), unknown accounts still pay the hash cost | CPU per login; fine at school scale |
| Session type | **Opaque server-side session** (random 256-bit token, SHA-256 stored in `auth_sessions`) | One DB lookup per request vs. JWT, but supports instant revocation, idle timeout and "sign out other sessions" |
| Transport | `HttpOnly`, `SameSite=Lax` cookie; `Secure` enforced in production | Needs same-site deployment (provided by the proxy) |
| CSRF | Synchronizer token: per-session random CSRF token (hash stored server-side), echoed by the client in `X-CSRF-Token`; plus `Origin` allow-list on unsafe methods and login | Client must read the non-HttpOnly CSRF cookie |
| Expiry | Absolute TTL (default 8 h) + idle timeout (default 60 min) | Configurable |
| Rate limiting | DB-backed: 5 failures per identifier / 50 per IP in 15 min, reset by a successful login | Works across workers; a WAF is still recommended |
| Error messages | One generic message for unknown ID, wrong password, wrong portal, inactive account | — |
| Portal check | Student portal → student accounts; Staff → staff; Director → management accounts that hold `mgmt.portal` | Entering via a portal grants nothing else |

Frontend route guards (`src/proxy.ts`, workspace shell) are **usability only**. Every API endpoint authorises
on the server through `app/api/deps.py` (account type + permission) and service-level assignment checks
(`app/services/teaching.py`).

### Prototype credential convention and the production path

The prototype seeds students with **Student ID + registered phone number** as the initial password, as
requested, through the local seed only (`app/seed/demo.py`, refuses to run when `APP_ENV=production`).
Every seeded account has `must_change_password = true`.

Before production:
1. Replace phone-based initial passwords with **random one-time activation codes** delivered through a
   verified channel (school office printout / SMS / email); store only hashes; expire them (e.g. 72 h).
2. Set `ENFORCE_PASSWORD_CHANGE=true` (already implemented: all endpoints except `/auth/me`,
   `/auth/logout`, `/auth/change-password` return `password_change_required`). Config validation already
   refuses to start production without it.
3. Add verified self-service recovery (email/SMS OTP with rate limits) — the UI currently says honestly that
   recovery is not connected.
4. Add **MFA (TOTP/WebAuthn)** for all management accounts and finance/HR staff.
5. Keep rate limiting, session revocation (already implemented on password change), and add breach-password
   checks and account lockout notifications.

## Authorisation model

* `permissions` is a global catalogue (`app/services/rbac.py`); `roles` are **school-owned** rows created from
  templates, so each school can tune them; `user_roles` links users to roles.
* Management roles are deliberately distinct: e.g. **Board Member** has aggregates only (no payroll,
  confidential complaints, invoices or audit log); **Technical Administrator** has configuration + audit only;
  **Principal** sees confidential complaints but not payroll.
* **Teaching access is assignment-based**, not role-based: a teacher only reaches sections/subjects in
  `teaching_assignments`; the class-teacher workspace appears only when a `class_teacher_assignments` row exists.
  One account holds both duties.
* The workspace/menu is computed by the backend (`app/services/workspace.py`) and returned by `/auth/me`.
* Sensitive reads are audited (e.g. `payroll.viewed`).

## Multi-tenancy (prepared, enforced and tested)

1. Every school-owned row has `school_id`.
2. **Composite foreign keys** `(school_id, x_id) → parent(school_id, id)` make cross-school references
   impossible at the database level.
3. **PostgreSQL row-level security** (migration `0002`) with `FORCE ROW LEVEL SECURITY` on all 55 tenant tables,
   keyed on the transaction-local `app.school_id`. With no tenant set, nothing is visible (default deny).
   The application role is `NOSUPERUSER NOBYPASSRLS` (tested).
4. The tenant is resolved from the **request hostname** against the trusted `school_domains` table — never from a
   browser-supplied school id. Sessions are looked up under RLS, so a session from school A is invisible at
   school B's host (tested).
5. The development fallback to a default school is rejected by configuration validation in production.

## Data governance

* Money: `NUMERIC(12,2)` everywhere, serialised as decimal strings; balances are **derived** from invoice lines,
  allocations, payments and refunds — there is no editable balance column. Paid/overdue status is derived.
* Time: all timestamps `timestamptz` (UTC); calendar facts (attendance day, due dates) are `date` in the school's
  timezone (`schools.timezone`, default Asia/Kolkata).
* Attendance: "Not recorded" is the absence of a record, never stored and never counted as an absence.
  Holidays/weekly offs are excluded. Corrections require a reason after submission and write
  `attendance_record_history`.
* Marks: unpublished results never reach students; corrections after publication require a reason and write
  `mark_history`; publication requires complete marks and writes an `approval_records` entry.
* `audit_events`, `attendance_record_history`, `mark_history`, `approval_records` are **append-only** (DB trigger).
* Lesson progression: completion is an explicit confirmed action (`confirm: true`); dismissing the prompt does
  nothing; completion is labelled as delivery, not mastery.
* Teacher evaluation: evidence (curriculum delivery, context averages, aggregated feedback with a minimum group
  size of 5) supports a **human** review; finalising requires every rubric criterion scored, a reviewer comment,
  and a reviewer other than the teacher.
* Anonymous feedback stores no user id (DB constraint).
* Confidential complaints can never be assigned to an individual teacher (DB constraint).

## Parent / guardian readiness

The model already contains `guardians` (optionally linked to a `users` row with `account_type='guardian'`) and
`student_guardians` with `verification_status`, `verified_by_user_id`, and per-link `can_view_academics` /
`can_view_fees` flags (a DB constraint requires a verifier for `verified`). To enable parent access:

1. Add a Parent portal entry + `portal="parent"` mapping to `account_type='guardian'`.
2. Add a `guardian_ctx` dependency that loads the guardian's **verified** links and an explicit "active child"
   chosen from that list (never a raw student id from the browser without checking the link).
3. Reuse the existing student services — they already take a `student_id` — after checking the link and its
   per-area flags. No change to the student module is required.

## White-label configuration

* **Branding and approved public content**: `frontend/src/config/schools/<slug>.ts`, validated with zod at build
  time (`schema.ts`). Colours flow into CSS variables → Tailwind tokens, so every component re-themes.
  Chart colours are a separate validated palette (`theme.chart`).
* **Operational settings** (modules, terminology, thresholds, grade scale, attendance policy, regional):
  `school_settings` JSONB validated by `app/schemas/settings.py`, versioned (optimistic locking) and audited.
* Next step for SaaS: serve public content from the backend/CMS per hostname instead of build-time files.

## Performance

Targets for one school of 500–2,000 profiles: p95 < 300 ms for dashboard endpoints at modest concurrency.
Measured locally on the seeded school (300 students, ~27k attendance records, 2 workers, 4 concurrent clients,
40 requests each): student dashboard p95 135 ms, teacher dashboard 95 ms, management overview 188 ms,
attendance analytics 144 ms, overdue invoice list 245 ms. Lists are paginated; aggregates are grouped in SQL;
batched lookups avoid N+1 queries; tenant-leading composite indexes back common queries.

Known hotspot: the invoice list derives status in Python after loading matching invoices; at larger scale move
derived balances into a SQL view/materialised summary.
