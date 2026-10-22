import { z } from "zod";

/**
 * Public (browser-visible) environment configuration, validated once at start-up.
 * Server-only settings such as BACKEND_URL are read in next.config.ts and never reach the browser.
 * Each variable must be referenced literally (process.env.NEXT_PUBLIC_X) so Next.js can inline it.
 */
const schema = z.object({
  schoolSlug: z.string().min(1),
  demoMode: z.boolean(),
  sessionCookieName: z.string().min(1),
  csrfCookieName: z.string().min(1),
});

export const env = schema.parse({
  schoolSlug: process.env.NEXT_PUBLIC_SCHOOL_SLUG ?? "demo",
  demoMode: process.env.NEXT_PUBLIC_DEMO_MODE === "true",
  sessionCookieName: process.env.NEXT_PUBLIC_SESSION_COOKIE_NAME ?? "erp_session",
  csrfCookieName: process.env.NEXT_PUBLIC_CSRF_COOKIE_NAME ?? "erp_csrf",
});
