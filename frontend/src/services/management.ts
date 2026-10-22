/** Management portal endpoints. Each one requires its own permission on the server. */
import { http, withQuery, type Page } from "@/lib/api/client";
import { queryDef } from "@/lib/api/query-def";
import type { Complaint, ComplaintStatusUpdate } from "./shared";

export interface Overview {
  data_label: string | null;
  as_of: string | null;
  kpis: {
    enrolled_students: number;
    active_staff: number;
    student_attendance_percent: number | null;
    staff_attendance_percent: number | null;
    average_score_percent: number | null;
    missing_attendance_registers: number;
    incomplete_assessments: number;
    pending_leave_requests: number;
    assessments_ready_to_publish: number;
    open_complaints: number;
    average_feedback_rating: number | null;
  };
  finance: {
    collected: string;
    outstanding: string;
    overdue_amount: string;
    overdue_invoices: number;
    collection_rate_percent: number | null;
  } | null;
  action_items: { severity: "high" | "medium" | "low"; text: string; href: string }[];
  recent_activity: { action: string; actor: string | null; created_at: string }[] | null;
  charts: {
    attendance_trend: { day: string; percent: number | null }[];
    subject_performance: { subject: string; average_percent: number; marks: number }[];
    score_distribution: { range: string; count: number }[];
    fee_collection: { month: string; amount: string }[] | null;
    exceptions: { label: string; count: number }[];
  };
}

export interface ManagementAssessment {
  id: string;
  name: string;
  section: string;
  subject: string;
  held_on: string;
  max_marks: string;
  is_published: boolean;
  entered: number;
  enrolled: number;
  complete: boolean;
}

export interface Academics {
  data_label: string | null;
  subject_performance: { subject: string; average_percent: number; marks: number }[];
  score_distribution: { range: string; count: number }[];
  grade_subject: { grade: number; subject: string; average_percent: number }[];
  assessments: Page<ManagementAssessment>;
  can_publish: boolean;
}

export interface AttendanceAnalytics {
  trend: { day: string; percent: number | null }[];
  staff_trend: { day: string; percent: number | null }[];
  by_section: {
    section: string;
    percent: number | null;
    present: number;
    late: number;
    absent: number;
    approved_leave: number;
    excused: number;
    recorded_days: number;
  }[];
  missing_registers: { section: string; day: string }[];
  students_below_threshold: number;
  threshold_percent: number;
}

export interface TeacherEvidence {
  year_elapsed_percent: number | null;
  guidance: string;
  teachers: {
    staff_id: string;
    staff_code: string;
    name: string;
    department: string;
    assignments: number;
    curriculum_delivery_percent: number | null;
    topics_pending: number;
    class_average_percent_context: number | null;
    topic_feedback_average: number | null;
    topic_feedback_responses: number;
    evaluations: number;
  }[];
}

export interface RubricCriterion {
  key: string;
  label: string;
  description: string;
  max_score: number;
}

export interface Evaluation {
  id: string;
  staff_name: string | null;
  period_label: string;
  status: string;
  scores: Record<string, number>;
  evidence_notes: string;
  reviewer_comment: string | null;
  finalized_at: string | null;
}

export interface Evaluations {
  rubric: { id: string; name: string; criteria: RubricCriterion[] };
  items: Evaluation[];
  can_manage: boolean;
}

export interface ComplaintsOverview {
  summary: { by_status: Record<string, number>; by_category: Record<string, number>; confidential_open: number };
  items: Complaint[] | null;
  can_manage: boolean;
  can_view_confidential: boolean;
}

export interface FeedbackSummary {
  categories: { category: string; responses: number; average_rating: number | null; suppressed: boolean }[];
  minimum_group_size: number;
  recent_comments: string[];
  note: string;
}

export interface AuditRow {
  id: string;
  action: string;
  actor: string | null;
  entity_type: string | null;
  details: Record<string, unknown>;
  ip: string | null;
  created_at: string;
}

export interface Enquiry {
  id: string;
  parent_name: string;
  email: string;
  phone: string;
  grade_sought: string;
  message: string | null;
  status: string;
  created_at: string;
}

export interface SchoolSettings {
  enabled_modules: string[];
  terminology: Record<string, string>;
  academic: {
    pass_percent: number;
    attendance_alert_percent: number;
    low_performance_percent: number;
    grade_scale: { min_percent: number; grade: string }[];
  };
  attendance: {
    weekly_off_days: number[];
    count_late_as_present: boolean;
    exclude_authorised_absence: boolean;
    correction_window_days: number;
    period_attendance_enabled: boolean;
  };
  regional: Record<string, string>;
}

export interface SchoolConfig {
  settings: SchoolSettings;
  version: number;
  can_manage: boolean;
}

export const managementApi = {
  overview: () => queryDef<Overview>("/management/overview"),
  academics: (status: string, page: number) => queryDef<Academics>(withQuery("/management/academics", { status, page, page_size: 15 })),
  attendance: () => queryDef<AttendanceAnalytics>("/management/attendance"),
  teacherEvidence: () => queryDef<TeacherEvidence>("/management/teachers"),
  evaluations: () => queryDef<Evaluations>("/management/evaluations"),
  complaints: (status: string) => queryDef<ComplaintsOverview>(withQuery("/management/complaints", { status })),
  feedback: () => queryDef<FeedbackSummary>("/management/feedback"),
  audit: (action: string, page: number) => queryDef<Page<AuditRow>>(withQuery("/management/audit", { action, page, page_size: 20 })),
  enquiries: (page: number) => queryDef<Page<Enquiry>>(withQuery("/management/enquiries", { page, page_size: 10 })),
  config: () => queryDef<SchoolConfig>("/management/config"),

  publishAssessment: (id: string) => http.post<{ published: boolean }>(`/management/assessments/${id}/publish`),
  createEvaluation: (body: { staff_id: string; period_label: string; evidence_notes: string }) =>
    http.post<{ id: string }>("/management/evaluations", { ...body, scores: {} }),
  scoreEvaluation: ({ id, scores }: { id: string; scores: Record<string, number> }) =>
    http.patch<{ ok: boolean }>(`/management/evaluations/${id}`, { scores }),
  finalizeEvaluation: ({ id, reviewer_comment }: { id: string; reviewer_comment: string }) =>
    http.post<{ ok: boolean }>(`/management/evaluations/${id}/finalize`, { reviewer_comment }),
  updateComplaint: ({ id, ...body }: { id: string } & ComplaintStatusUpdate) =>
    http.post<{ ok: boolean }>(`/management/complaints/${id}/update`, body),
  saveConfig: (body: { version: number; settings: SchoolSettings }) =>
    http.put<{ ok: boolean; version: number }>("/management/config", body),
};
