/**
 * Client-side validation for instant feedback. The backend re-validates everything and is the
 * authority; these rules mirror its limits so users see problems before submitting.
 * Each validator returns a map of field -> message (empty when valid).
 */

export type Errors<K extends string> = Partial<Record<K, string>>;

export const hasErrors = (e: Record<string, string | undefined>) => Object.values(e).some(Boolean);

const LOGIN_ID = /^[A-Za-z0-9-]{3,32}$/;
const INDIAN_MOBILE = /^[6-9]\d{9}$/;
const EMAIL = /^\S+@\S+\.\S+$/;
export const MIN_PASSWORD_LENGTH = 10;
export const MIN_REASON_LENGTH = 5;

export function validateLogin(v: { loginId: string; password: string }, idLabel: string): Errors<"loginId" | "password"> {
  const e: Errors<"loginId" | "password"> = {};
  const id = v.loginId.trim();
  if (!id) e.loginId = `Enter your ${idLabel}.`;
  else if (!LOGIN_ID.test(id)) e.loginId = `${idLabel} can only contain letters, numbers and hyphens.`;
  if (!v.password) e.password = "Enter your password.";
  return e;
}

export function validateEnquiry(v: { parent_name: string; email: string; phone: string; grade_sought: string }) {
  const e: Errors<"parent_name" | "email" | "phone" | "grade_sought"> = {};
  if (v.parent_name.trim().length < 2) e.parent_name = "Enter your name.";
  if (!EMAIL.test(v.email)) e.email = "Enter a valid email address.";
  if (!INDIAN_MOBILE.test(v.phone)) e.phone = "Enter a 10-digit Indian mobile number.";
  if (!v.grade_sought) e.grade_sought = "Choose a grade.";
  return e;
}

export function validatePasswordChange(v: { current: string; next: string; confirm: string }) {
  const e: Errors<"current" | "next" | "confirm"> = {};
  if (!v.current) e.current = "Enter your current password.";
  if (v.next.length < MIN_PASSWORD_LENGTH) e.next = `Use at least ${MIN_PASSWORD_LENGTH} characters.`;
  else if (!/[A-Za-z]/.test(v.next) || !/\d/.test(v.next)) e.next = "Include both letters and numbers.";
  if (v.next !== v.confirm) e.confirm = "Passwords do not match.";
  return e;
}

export function validateLeave(v: { starts_on: string; ends_on: string; reason: string }) {
  const e: Errors<"starts_on" | "ends_on" | "reason"> = {};
  if (!v.starts_on) e.starts_on = "Choose a start date.";
  if (!v.ends_on) e.ends_on = "Choose an end date.";
  else if (v.starts_on && v.ends_on < v.starts_on) e.ends_on = "End date cannot be before start date.";
  if (v.reason.trim().length < 3) e.reason = "Give a short reason.";
  return e;
}

export function validateComplaint(v: { category: string; subject: string; description: string }) {
  const e: Errors<"category" | "subject" | "description"> = {};
  if (!v.category) e.category = "Choose a category.";
  if (v.subject.trim().length < 5) e.subject = "Use at least 5 characters.";
  if (v.description.trim().length < 10) e.description = "Describe the issue in at least 10 characters.";
  return e;
}

export function validateFeedback(v: { category: string; rating: string }) {
  const e: Errors<"category" | "rating"> = {};
  if (!v.category) e.category = "Choose a category.";
  if (!v.rating) e.rating = "Choose a rating.";
  return e;
}

export function validateMessage(v: { staff_id: string; subject: string; body: string }) {
  const e: Errors<"staff_id" | "subject" | "body"> = {};
  if (!v.staff_id) e.staff_id = "Choose a teacher.";
  if (v.subject.trim().length < 3) e.subject = "Add a short subject (3+ characters).";
  if (!v.body.trim()) e.body = "Write your message.";
  return e;
}

export function validateAssessment(v: { name: string; held_on: string; max_marks: string }): string | null {
  if (v.name.trim().length < 3 || !v.held_on || !(Number(v.max_marks) > 0)) {
    return "Enter a name (3+ characters), a date and maximum marks above 0.";
  }
  return null;
}

/** Returns the ids whose entered mark is not a number within 0..max (blank means "not entered"). */
export function invalidMarks(values: Record<string, string>, max: number): string[] {
  return Object.entries(values)
    .filter(([, v]) => v !== "" && (Number.isNaN(Number(v)) || Number(v) < 0 || Number(v) > max))
    .map(([id]) => id);
}

export function validatePaymentAmount(amount: string, balance: string): string | null {
  const a = Number(amount);
  return a > 0 && a <= Number(balance) ? null : `Enter an amount greater than 0 and at most the outstanding balance.`;
}

/** Corrections to submitted/published records must explain why. */
export function validateReason(reason: string): string | null {
  return reason.trim().length >= MIN_REASON_LENGTH ? null : `Give a reason (at least ${MIN_REASON_LENGTH} characters).`;
}
