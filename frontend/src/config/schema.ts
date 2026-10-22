import { z } from "zod";

/**
 * White-label school configuration. Branding and approved public content live here;
 * access control and business rules never do (those are enforced by the backend).
 */
const hex = z.string().regex(/^#[0-9a-fA-F]{6}$/, "Use a 6-digit hex colour");
const iconKey = z.enum([
  "book",
  "flask",
  "laptop",
  "trophy",
  "music",
  "bus",
  "library",
  "shield",
  "users",
  "heart",
  "graduation",
  "palette",
  "globe",
  "leaf",
  "stethoscope",
  "utensils",
]);

export const schoolConfigSchema = z.object({
  slug: z.string().min(1),
  name: z.string().min(3),
  shortName: z.string().min(2),
  tagline: z.string(),
  affiliation: z.string(),
  established: z.number().int().min(1800),
  isFictional: z.boolean(),
  logo: z.object({ src: z.string(), alt: z.string() }),
  favicon: z.string(),
  theme: z.object({
    primary: hex,
    primaryContrast: hex,
    secondary: hex,
    surface: hex,
    radius: z.enum(["sm", "md", "lg"]),
    /** Chart mark colours, validated for lightness, chroma and colour-vision separation. */
    chart: z.array(hex).min(1),
  }),
  regional: z.object({ locale: z.string(), currency: z.string().length(3), timezone: z.string() }),
  terminology: z.object({ student: z.string(), staff: z.string(), director: z.string(), portal: z.string() }),
  contact: z.object({
    addressLines: z.array(z.string()).min(1),
    phone: z.string(),
    email: z.string().email(),
    officeHours: z.string(),
  }),
  content: z.object({
    hero: z.object({ eyebrow: z.string(), title: z.string(), subtitle: z.string() }),
    stats: z.array(z.object({ label: z.string(), value: z.string() })),
    highlights: z.array(z.object({ icon: iconKey, title: z.string(), text: z.string() })),
    about: z.object({
      intro: z.string(),
      vision: z.string(),
      mission: z.array(z.string()),
      principalMessage: z.object({ name: z.string(), role: z.string(), message: z.string() }),
      milestones: z.array(z.object({ year: z.string(), text: z.string() })),
    }),
    academics: z.object({
      intro: z.string(),
      stages: z.array(z.object({ name: z.string(), grades: z.string(), focus: z.string() })),
      subjects: z.array(z.string()),
      assessment: z.string(),
    }),
    admissions: z.object({
      intro: z.string(),
      steps: z.array(z.object({ title: z.string(), text: z.string() })),
      documents: z.array(z.string()),
      dates: z.array(z.object({ label: z.string(), value: z.string() })),
      feeNote: z.string(),
    }),
    facilities: z.array(z.object({ icon: iconKey, title: z.string(), text: z.string() })),
    faculty: z.array(z.object({ name: z.string(), role: z.string(), department: z.string(), qualification: z.string() })),
    news: z.array(z.object({ date: z.string(), title: z.string(), summary: z.string(), kind: z.enum(["news", "notice", "event"]) })),
  }),
});

export type SchoolConfig = z.infer<typeof schoolConfigSchema>;
export type IconKey = z.infer<typeof iconKey>;
