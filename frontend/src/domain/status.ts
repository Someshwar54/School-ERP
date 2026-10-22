/** Mapping of record states to badge tones, so every screen colours the same state the same way. */

export type Tone = "info" | "success" | "warning" | "error" | "neutral";
export type TopicStatus = "planned" | "in_progress" | "pending" | "completed";

export const INVOICE_TONE: Record<string, Tone> = {
  paid: "success",
  partially_paid: "info",
  unpaid: "warning",
  overdue: "error",
  cancelled: "neutral",
};
export const COMPLAINT_TONE: Record<string, Tone> = { open: "warning", in_review: "info", resolved: "success", closed: "neutral" };
export const LEAVE_TONE: Record<string, Tone> = { pending: "warning", approved: "success", rejected: "error", cancelled: "neutral" };
export const TOPIC_TONE: Record<TopicStatus, Tone> = { planned: "neutral", in_progress: "info", pending: "warning", completed: "success" };
export const SEVERITY_TONE: Record<"high" | "medium" | "low", Tone> = { high: "error", medium: "warning", low: "info" };

export function assessmentState(a: { is_published: boolean; complete: boolean }): { label: string; tone: Tone } {
  if (a.is_published) return { label: "Published", tone: "success" };
  return a.complete ? { label: "Ready", tone: "info" } : { label: "Incomplete", tone: "warning" };
}
