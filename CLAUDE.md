# Working in this repository

School website + School ERP prototype. FastAPI + PostgreSQL backend (`backend/`), Next.js frontend (`frontend/`).
Read `docs/CONVENTIONS.md` before changing code; `docs/BACKEND.md` / `docs/FRONTEND.md` have
"add a feature" checklists.

## Rules that must hold

- Backend layering: routes (`app/api/v1/routes`) are thin → services (`app/services`) hold business rules →
  models. Request/response models live in `app/schemas`. Services never import FastAPI or `app.api`.
- Every school-owned table has `school_id`, composite same-school foreign keys and row-level security.
  New tenant tables must be added to an RLS migration (tests fail otherwise).
- Authorisation is enforced on the server for every endpoint. Frontend checks are UX only.
- Frontend layering: `app/` routes render `features/`; data access only through `src/services` +
  `useApiQuery`/`useApiMutation`; pure rules in `src/domain`; primitives in `components/ui`.
  Never call `fetch` from features (ESLint enforces this).
- Money is Decimal / decimal strings, never float. Errors use the `{"error": {...}}` envelope.
- Demo data is fictional and local-only; never add real personal data or credentials to code.

## Commands

```bash
# backend (from backend/)
.venv/bin/pytest                              # tests (uses env/test.env, database school_erp_test)
.venv/bin/ruff check app tests && .venv/bin/ruff format --check app tests && .venv/bin/mypy app
.venv/bin/python -m app.tools.export_openapi  # refresh docs/API_ENDPOINTS.md after API changes

# frontend (from frontend/)
npm run check                                  # typecheck + lint + prettier + unit tests
PLAYWRIGHT_CHROMIUM_PATH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome npm run test:e2e
```
