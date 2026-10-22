/** Student workspace endpoints. All are scoped server-side to the signed-in student. */
import { http } from "@/lib/api/client";
import { queryDef } from "@/lib/api/query-def";
import type { AttendanceStatus } from "@/domain/attendance";
import type { Announcement, Complaint, DocumentRecord, MessageThread, MessageThreadDetail, TimetableData } from "./shared";

export interface AttendanceSummary {
  present: number;
  late: number;
  absent: number;
  approved_leave: number;
  excused: number;
  recorded_days: number;
  percent: number | null;
}

export interface StudentDashboard {
  student: { name: string; student_code: string; section: string | null; roll_no: number | null };
  attendance: AttendanceSummary;
  recent_results: {
    assessment: string;
    subject: string;
    marks_obtained: string | null;
    max_marks: string;
    percent: number | null;
    grade: string | null;
    status: string;
  }[];
  today_classes: { id: string; period_no: number; subject: string; teacher: string | null; room: string | null }[];
  periods: { period_no: number; starts_at: string; ends_at: string }[];
  fees: { outstanding: string; next_due: { invoice_no: string; due_on: string; balance: string } | null };
  announcements: Announcement[];
  events: { id: string; title: string; starts_at: string; location: string }[];
}

export interface StudentProfile {
  student_code: string;
  admission_no: string;
  name: string;
  date_of_birth: string;
  gender: string;
  admission_date: string;
  blood_group: string | null;
  address: string | null;
  email: string | null;
  phone_masked: string;
  section: string | null;
  roll_no: number | null;
  guardians: { name: string; relationship: string; verification: string; is_primary: boolean }[];
  note: string;
}

export type CalendarDayStatus = AttendanceStatus | "not_recorded" | "holiday" | "weekly_off" | "upcoming" | "outside_year";

export interface AttendanceMonth {
  month: string;
  days: {
    day: string;
    status: CalendarDayStatus;
    holiday_name: string | null;
    remark: string | null;
    periods: { period_no: number; status: string }[];
  }[];
  month_summary: AttendanceSummary;
  year_summary: AttendanceSummary;
  not_recorded_days: number;
  trend: ({ month: string } & AttendanceSummary)[];
  policy: { late_counts_as_present: boolean; authorised_absence_excluded: boolean; alert_below_percent: number };
}

export interface SubjectPerformance {
  subject: string;
  assessments: number;
  scored: number;
  average_percent: number | null;
  insufficient_data: boolean;
  trend: { assessment: string; percent: number | null }[];
}

export interface Performance {
  subjects: SubjectPerformance[];
  overall_percent: number | null;
  insufficient_data: boolean;
}

export interface Results {
  exams: {
    assessment: string;
    held_on: string;
    total: number;
    maximum: number;
    percent: number | null;
    subjects: {
      subject: string;
      marks_obtained: string | null;
      max_marks: string;
      percent: number | null;
      grade: string | null;
      status: string;
      remarks: string | null;
    }[];
  }[];
  note: string;
}

export interface Ledger {
  invoices: {
    id: string;
    invoice_no: string;
    term: string | null;
    issued_on: string;
    due_on: string;
    status: string;
    net: string;
    paid: string;
    balance: string;
    concessions: string;
    lines: { description: string; line_type: string; amount: string }[];
  }[];
  payments: {
    id: string;
    receipt_no: string;
    amount: string;
    paid_on: string;
    method: string;
    reference: string | null;
    allocations: { invoice_no: string | null; amount: string }[];
  }[];
  refunds: { receipt_no: string; amount: string; refunded_on: string; reason: string }[];
  totals: { billed: string; concessions: string; paid: string; refunded: string; outstanding: string };
  next_due: { invoice_no: string; due_on: string; balance: string } | null;
}

export interface StudentDocuments {
  report_cards: { term_id: string; term: string; available: boolean }[];
  documents: DocumentRecord[];
  storage_note: string;
}

export interface ReportCard {
  term: string;
  student: { name: string; student_code: string; section: string | null; roll_no: number | null; admission_no: string };
  subjects: SubjectPerformance[];
  attendance: AttendanceSummary;
  generated_note: string;
}

export interface StudentTopic {
  id: string;
  subject: string;
  title: string;
  status: string;
  my_feedback: { understanding: number; comment: string | null } | null;
}

export interface AssignedTeacher {
  staff_id: string;
  name: string;
  subject: string;
  is_class_teacher: boolean;
}

export interface ComplaintInput {
  category: string;
  subject: string;
  description: string;
  is_confidential: boolean;
}

export interface FeedbackInput {
  category: string;
  rating: number;
  comment: string | null;
  is_anonymous: boolean;
}

export const studentApi = {
  dashboard: () => queryDef<StudentDashboard>("/student/dashboard"),
  profile: () => queryDef<StudentProfile>("/student/profile"),
  attendance: (month: string) => queryDef<AttendanceMonth>(`/student/attendance?month=${month}`),
  performance: () => queryDef<Performance>("/student/performance"),
  results: () => queryDef<Results>("/student/results"),
  timetable: () => queryDef<TimetableData>("/student/timetable"),
  fees: () => queryDef<Ledger>("/student/fees"),
  documents: () => queryDef<StudentDocuments>("/student/documents"),
  reportCard: (termId: string) => queryDef<ReportCard>(`/student/report-card/${termId}`),
  teachers: () => queryDef<AssignedTeacher[]>("/student/teachers"),
  threads: () => queryDef<MessageThread[]>("/student/messages"),
  thread: (id: string) => queryDef<MessageThreadDetail>(`/student/messages/${id}`),
  complaints: () => queryDef<Complaint[]>("/student/complaints"),
  topics: () => queryDef<StudentTopic[]>("/student/topics"),

  createThread: (body: { staff_id: string; subject: string; body: string }) => http.post<{ id: string }>("/student/messages", body),
  reply: ({ threadId, body }: { threadId: string; body: string }) =>
    http.post<{ ok: boolean }>(`/student/messages/${threadId}/reply`, { body }),
  createComplaint: (body: ComplaintInput) =>
    http.post<{ id: string; reference_no: string; routed_to: string }>("/student/complaints", body),
  giveTopicFeedback: ({ topicId, understanding }: { topicId: string; understanding: number }) =>
    http.post<{ ok: boolean }>(`/student/topics/${topicId}/feedback`, { understanding, share_name: true }),
  createFeedback: (body: FeedbackInput) => http.post<{ ok: boolean; anonymous: boolean }>("/student/feedback", body),
};
