import { schoolConfigSchema, type SchoolConfig } from "./schema";
import { demoSchool } from "./schools/demo";

const registry: Record<string, SchoolConfig> = { demo: demoSchool };

/**
 * The deployed school is chosen at build time via NEXT_PUBLIC_SCHOOL_SLUG and validated,
 * so a broken configuration fails the build rather than rendering a half-branded site.
 */
function load(): SchoolConfig {
  const slug = process.env.NEXT_PUBLIC_SCHOOL_SLUG ?? "demo";
  const config = registry[slug];
  if (!config) throw new Error(`Unknown school configuration: ${slug}`);
  return schoolConfigSchema.parse(config);
}

export const school = load();

const radius = { sm: "0.375rem", md: "0.625rem", lg: "0.875rem" } as const;

/** CSS custom properties consumed by Tailwind theme tokens in globals.css. */
export function themeVariables(config: SchoolConfig = school): Record<string, string> {
  return {
    "--brand": config.theme.primary,
    "--brand-contrast": config.theme.primaryContrast,
    "--accent": config.theme.secondary,
    "--surface": config.theme.surface,
    "--radius": radius[config.theme.radius],
  };
}
