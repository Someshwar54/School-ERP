# Conventions

These rules keep the codebase predictable as it grows. Several are enforced automatically
(see "Enforced by" in each section); the rest are checked in review.

## Naming

| Thing | Convention | Example |
|---|---|---|
| Python modules, functions, variables | `snake_case` | `staff_self_service.py`, `list_my_leave()` |
| Python classes | `PascalCase` | `AuthContext`, `LeaveRequest` |
| Service functions | `verb_noun`: `get_*` (one thing/view), `list_*` (collections), `create_*`, `update_*`, `record_*`, `decide_*`, `publish_*` | `get_dashboard`, `list_invoices`, `record_payment` |
| Request schemas | `<Thing>Create`, `<Thing>Update`, `<Thing>Submission`, `<Thing>Decision` | `LeaveCreate`, `ComplaintStatusUpdate` |
| Response schemas | `<Thing>Response` | `MeResponse`, `LoginResponse` |
| Database tables | plural `snake_case` | `attendance_records` |
| API paths | plural nouns, kebab-case, verbs only for actions | `/hr/leave-requests/{id}/decision` |
| TypeScript files | `kebab-case` | `finance-view.tsx`, `use-session.ts` |
| React components | `PascalCase`; route screens end in `Page` | `TeacherMarksPage`, `DocumentTable` |
| Hooks | `useX`, file `use-x.ts` | `useApiQuery`, `use-today.ts` |
| Service objects (frontend) | `<domain>Api` with methods named after the action | `teacherApi.saveRegister` |
| Domain constants | `SCREAMING_SNAKE_CASE` | `LEAVE_TYPES`, `INVOICE_TONE` |
| Environment variables | `SCREAMING_SNAKE_CASE`; browser-visible ones start `NEXT_PUBLIC_` | `BACKEND_URL`, `NEXT_PUBLIC_SCHOOL_SLUG` |

## Layering

Backend: `api (routes) → services → models`. Schemas are shared by both. Services never import
FastAPI or `app.api`. *Enforced by:* `backend/tests/test_structure.py`.

Frontend: `app (routes) → features → services + domain + components/ui`. Only `src/services` knows
API URLs; only `src/lib/api` performs HTTP. *Enforced by:* ESLint rules in `frontend/eslint.config.mjs`.

## Errors

* Backend: raise `AppError` (or the `not_found` / `forbidden` / `bad_request` helpers) from services.
  Never return error dicts. Every error leaves the API as `{"error": {"code", "message", "details?"}}`.
  Messages are written for end users; never include SQL, stack traces or whether an account exists.
* Frontend: queries surface errors through `DataState`; mutations expose `.error`. Show `error.message`
  (already user-facing). Render-time crashes are caught by the workspace `ErrorBoundary` and `app/error.tsx`.

## Money, time and IDs

* Money is `Decimal` in Python, `NUMERIC(12,2)` in PostgreSQL and a decimal **string** in JSON. Never float.
* Timestamps are timezone-aware UTC (`timestamptz`); calendar facts (attendance day, due date) are `date`
  in the school's timezone. Weekdays are Monday = 0 on both sides (`weekdayIndex`).
* Primary keys are UUIDs; school-owned tables always carry `school_id`.

## Formatting and checks

| Area | Command |
|---|---|
| Backend lint + format | `ruff check app tests && ruff format --check app tests` |
| Backend types | `mypy app` |
| Backend tests | `pytest` |
| Frontend everything (types, lint, format, unit tests) | `npm run check` |
| Browser tests | `npm run test:e2e` |

## Comments and docs

* Every module starts with a one-line docstring/comment saying what it is responsible for.
* Comment *why* (a rule, a security reason, a trade-off), not *what*.
* When you add an endpoint, regenerate `docs/API_ENDPOINTS.md` with `python -m app.tools.export_openapi`.
