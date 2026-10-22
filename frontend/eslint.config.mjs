import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

/**
 * Architecture rules (see docs/FRONTEND.md):
 *   app/        routes only; render features
 *   features/   screens; get data via services + lib/api/query hooks, never fetch directly
 *   services/   typed API endpoints (the only place that knows URLs)
 *   domain/     pure business rules: no React, no Next.js, no network
 *   components/ui  presentational primitives: no data access, no features
 */
const noDirectHttp = {
  "@typescript-eslint/no-restricted-imports": [
    "error",
    {
      patterns: [
        {
          group: ["@/lib/api/client"],
          allowTypeImports: true,
          message: "Call an endpoint from src/services instead of the raw HTTP client.",
        },
      ],
    },
  ],
  "no-restricted-globals": ["error", { name: "fetch", message: "Use src/services + useApiQuery/useApiMutation instead of fetch()." }],
};

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  { files: ["src/app/**", "src/features/**"], rules: noDirectHttp },
  {
    files: ["src/components/ui/**"],
    rules: {
      "@typescript-eslint/no-restricted-imports": [
        "error",
        {
          patterns: [
            { group: ["@/services/*", "@/features/*"], message: "UI primitives must not depend on features or data access." },
            { group: ["@/lib/api/*"], allowTypeImports: true, message: "UI primitives may only import API types." },
          ],
        },
      ],
    },
  },
  {
    files: ["src/domain/**"],
    rules: {
      "@typescript-eslint/no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["react", "react-dom", "next", "next/*", "@/lib/api/*", "@/services/*"],
              message: "Domain rules must stay pure (no React, Next.js or network).",
            },
          ],
        },
      ],
    },
  },
  globalIgnores([".next/**", ".next-e2e/**", "out/**", "build/**", "next-env.d.ts", "test-results/**", "playwright-report/**"]),
]);

export default eslintConfig;
