# API contract

Base path: **`/api/v1`**. The browser calls it on the frontend's own origin (`/api/*` is proxied to
FastAPI), so the session cookie is first-party. Full endpoint list: [API_ENDPOINTS.md](API_ENDPOINTS.md)
(generated). Machine-readable schema: [openapi.json](openapi.json). Interactive docs in development:
`http://localhost:8000/api/docs`.

## Versioning

Routes live in `backend/app/api/v1/routes/<domain>.py` and are mounted by `app/api/v1/__init__.py`.
Additive changes (new endpoints, new optional fields) stay in v1. A breaking change gets a new package
`app/api/v2` mounted at `/api/v2`, while v1 keeps serving existing clients until retired.

## Authentication and tenancy

| Concern | Rule |
|---|---|
| Tenant | Resolved from the request hostname via the `school_domains` table. Never from a client-supplied id. |
| Sign-in | `POST /auth/login {portal, login_id, password}` sets `erp_session` (HttpOnly) and `erp_csrf` cookies. |
| Session | Opaque token, SHA-256 stored server-side; absolute TTL + idle timeout; revocable. |
| CSRF | Every non-GET request must send `X-CSRF-Token: <erp_csrf cookie>`; `Origin` must be allow-listed. |
| Authorisation | Account type + permission per endpoint, plus assignment checks inside services. |

## Errors

Every error uses one envelope:

```json
{ "error": { "code": "validation_error", "message": "Some fields are invalid.",
             "details": [{ "field": "phone", "message": "String should match pattern '^[6-9]\\d{9}$'" }] } }
```

| Status | Typical `code` | Meaning |
|---|---|---|
| 400 | `invalid_request`, `reason_required`, `confirmation_required`, `weak_password`, … | Request understood but breaks a business rule |
| 401 | `unauthenticated`, `invalid_credentials` | Not signed in / session expired / wrong credentials (generic) |
| 403 | `forbidden`, `csrf_failed`, `password_change_required` | Not allowed for this account |
| 404 | `not_found`, `unknown_school` | Missing, or not visible to this account |
| 409 | `conflict`, `version_conflict`, `incomplete_marks`, `exceeds_balance`, … | Conflicts with current state |
| 422 | `validation_error` | Input failed schema validation (`details` lists fields) |
| 429 | `rate_limited` | Too many attempts |
| 503 | `service_unavailable` | Database unavailable |
| 500 | `internal_error` | Unexpected; logged with the request id (`x-request-id` header) |

## Conventions

* Lists that can grow are paginated: `?page=1&page_size=25` (max 100) → `{items, total, page, page_size}`.
* Money is a decimal string (`"1234.50"`); dates are `YYYY-MM-DD`; timestamps are ISO 8601 UTC.
* IDs are UUIDs. Student-scoped endpoints never accept a student id: they use the signed-in student.
* Health: `GET /health` (liveness), `GET /health/ready` (database + schema version).
