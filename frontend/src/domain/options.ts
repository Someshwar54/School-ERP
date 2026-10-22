/** Option lists that mirror backend enums (see backend model CHECK constraints). Defined once here. */

export const COMPLAINT_CATEGORIES = ["academic", "facilities", "transport", "conduct", "fees", "other"] as const;
export const FEEDBACK_CATEGORIES = ["teaching", "facilities", "transport", "communication", "general"] as const;
export const LEAVE_TYPES = ["casual", "sick", "earned", "unpaid"] as const;
export const ASSESSMENT_KINDS = ["unit_test", "half_yearly", "annual", "assignment", "practical"] as const;
export const ADMISSION_GRADES = ["Grade 6", "Grade 7", "Grade 8", "Grade 9"] as const;
export const ERP_MODULES = [
  "attendance",
  "academics",
  "timetable",
  "fees",
  "announcements",
  "events",
  "documents",
  "messaging",
  "complaints",
  "feedback",
  "lesson_progress",
  "library",
  "transport",
  "payroll",
] as const;
/** Topic-understanding scale used by student topic feedback (1–5). */
export const UNDERSTANDING_LEVELS = ["", "Very unclear", "Unclear", "Okay", "Clear", "Very clear"] as const;
