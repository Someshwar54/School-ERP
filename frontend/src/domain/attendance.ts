/** Attendance rules shared by the student calendar and the teacher register. */

export type AttendanceStatus = "present" | "absent" | "late" | "approved_leave" | "excused";

export const ATTENDANCE_OPTIONS: { value: AttendanceStatus; label: string; short: string }[] = [
  { value: "present", label: "Present", short: "P" },
  { value: "absent", label: "Absent", short: "A" },
  { value: "late", label: "Late", short: "L" },
  { value: "approved_leave", label: "Approved leave", short: "AL" },
  { value: "excused", label: "Excused", short: "EX" },
];

/** Count how many students hold each status in a register being edited. */
export function countByStatus(marks: Record<string, AttendanceStatus | null>): Record<AttendanceStatus, number> {
  const counts = { present: 0, absent: 0, late: 0, approved_leave: 0, excused: 0 } as Record<AttendanceStatus, number>;
  for (const s of Object.values(marks)) if (s) counts[s] += 1;
  return counts;
}

export function unmarkedCount(marks: Record<string, AttendanceStatus | null>): number {
  return Object.values(marks).filter((m) => !m).length;
}

/** Shift a "YYYY-MM" month by `delta` months. */
export function shiftMonth(month: string, delta: number): string {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(Date.UTC(y, m - 1 + delta, 1));
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}

/** Monday-based weekday index (0 = Monday) of a calendar date "YYYY-MM-DD". Matches the backend. */
export function weekdayIndex(isoDate: string): number {
  const [y, m, d] = isoDate.split("-").map(Number);
  return (new Date(Date.UTC(y, m - 1, d)).getUTCDay() + 6) % 7;
}
