# Frontend guide (Next.js)

## Layout and layering

```
frontend/src/
├── app/                 ROUTES ONLY: layouts, metadata and one-line pages that render a feature
│   ├── (site)/          public website routes
│   ├── erp/             portal entry, sign-in pages, recovery, student/staff/management workspaces
│   ├── error.tsx, global-error.tsx, not-found.tsx   error boundaries and 404
├── features/            SCREENS, grouped by area (UI + wiring, no raw HTTP)
│   ├── site/            public website sections, header/footer, enquiry form
│   ├── auth/            portal frame, login form/page, session hooks (useSession, useSignOut)
│   ├── workspace/       ERP shell (header, server-driven nav, error boundary)
│   ├── common/          features shared by several workspaces: announcements, events, account settings,
│   │                    messages, complaints, documents, timetable, ledger, finance, HR, planned modules
│   ├── student/ teacher/ staff/ management/   workspace screens (*-page.tsx)
├── services/            TYPED API LAYER: one module per backend domain; DTO types + endpoints
├── domain/              PURE BUSINESS RULES: validation, attendance rules, option lists, status→tone
├── components/
│   ├── ui/              reusable primitives (Button, Card, Field, Table, Dialog, Tabs, DataState, ErrorBoundary…)
│   └── charts/          lazy Plotly wrapper with validated palette and table fallback
├── lib/                 api/client.ts (fetch + CSRF + ApiError), api/query.ts (state hooks), format, cn
├── hooks/               generic hooks (useTodayISO)
├── providers/           AppProviders (QueryClientProvider)
├── config/              env.ts (validated public env), school.ts + schools/<slug>.ts (white-label config)
└── proxy.ts             UX-only redirect to sign-in when no session cookie
```

Dependency direction: `app → features → (services, domain, components, lib, hooks, config)`.
ESLint enforces the important edges:

* `features/` and `app/` may not call `fetch` or import the raw HTTP client — use `services/`.
* `components/ui/` may not import features or services (only API *types*).
* `domain/` may not import React, Next.js, services or the API client (keeps it unit-testable).

## State management

Server state uses **TanStack Query** through two hooks in `lib/api/query.ts`:

```tsx
const state = useApiQuery(teacherApi.topics(assignment));          // cached, de-duplicated read
const save = useApiMutation(teacherApi.saveMarks, {                 // write …
  invalidates: ["/teacher/assessments", "/teacher/dashboard"],      // … then refresh every cached read
});                                                                 //     whose API path starts with these
<DataState state={state}>{(data) => …}</DataState>                  // consistent loading / error / empty
```

* Query keys are API paths, so invalidating `"/finance"` refreshes the summary, invoice list and ledgers.
* 4xx errors are not retried; transient failures are retried once.
* Any 401 dispatches one global event; the workspace shell clears the cache and redirects to sign-in.
* The cache is cleared on sign-in and sign-out so one user's data is never shown to the next.
* Session: `useSession()` reads `/auth/me` from the same cache (`me`, `can(permission)`), no context needed.
* Local UI state (form fields, selected tab) stays in `useState` inside the component that owns it.

## Adding a screen (checklist)

1. **Types + endpoint** in `src/services/<domain>.ts` (`queryDef<T>(path)` for reads, `http.post/put/patch` for writes).
2. **Rules** that are not presentation (validation, derived states, option lists) in `src/domain/`, with a unit test.
3. **Screen** in `src/features/<area>/<name>-page.tsx` exporting `<Area><Name>Page`, using `useApiQuery`,
   `useApiMutation`, `DataState` and `components/ui`.
4. **Route** `src/app/erp/<workspace>/<name>/page.tsx`: metadata title + `return <XPage />`.
5. **Navigation**: label/icon/route in `features/workspace/nav.ts`; the backend decides visibility via
   `services/workspace.py` (`/auth/me` → `workspace.modules`).
6. **Tests**: `npm run check`; add a Playwright test for important flows.

## Error handling

| Where | Mechanism |
|---|---|
| Failed request | `ApiError` (status, code, user-facing message, field details) from `lib/api/client.ts` |
| Read failed | `DataState` shows `ErrorState` (403 → "Access restricted"; others → message + Try again) |
| Write failed | `mutation.error.message` in an `Alert` next to the form |
| Invalid input | `domain/validation.ts` field errors before submit; backend 422 is the authority |
| Render crash | `ErrorBoundary` around each workspace page (navigation keeps working); `app/error.tsx`; `app/global-error.tsx` |
| Unknown route | `app/not-found.tsx` |

## Environment

| File | Purpose |
|---|---|
| `.env.development` | Committed dev defaults (`BACKEND_URL`, school slug, demo mode) |
| `.env.local` | Personal overrides (git-ignored) |
| `.env.production.example` | Template for hosting configuration |

`BACKEND_URL` is server-only (used by the `/api` rewrite). `NEXT_PUBLIC_*` values are validated in
`src/config/env.ts` and inlined at build time. Never put secrets in `NEXT_PUBLIC_*`.
