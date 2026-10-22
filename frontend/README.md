# Frontend (Next.js)

Public school website + ERP portal UI. Setup and demo accounts: [README](../README.md).
Structure, layer rules, state management and the "add a screen" checklist: [docs/FRONTEND.md](../docs/FRONTEND.md).

```bash
npm run dev        # http://localhost:3000 (expects the backend on :8000, see .env.development)
npm run check      # typecheck + lint (incl. architecture rules) + prettier + unit tests
npm run build      # production build
npm run test:e2e   # Playwright against a production build + throwaway backend
```
