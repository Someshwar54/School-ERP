/** Teacher workspace endpoints. The backend checks every class/subject against the teacher's assignments. */
import { http, withQuery } from "@/lib/api/client";
import { queryDef } from "@/lib/api/query-def";
import type { AttendanceStatus } from "@/domain/attendance";
import type { TopicStatus } from "@/domain/status";
import type { Announcement, Complaint, ComplaintStatusUpdate, MessageThread, MessageThreadDetail, TimetableData } from "./shared";

export interface Assignment {
  section_id: string;
  section: string;
  subject_id: string;
  subject: string;
}

export interface RosterStudent {
  student_id: string;
  student_code: string;
  name: string;
  roll_no: number;
}

export interface TeacherDashboard {
  assignments: { section: string; subject: string }[];
  class_teacher_of: { section_id: string; section: string }[];
  today_periods: LessonPrompt[];
  pending: {
    missing_registers: { section: string; section_id: string; day: string }[];
    incomplete_assessments: { assessment_id: string; name: string; section: string; missing: number }[];
    assigned_complaints: number;
  };
  duties: { title: string; duty_date: string }[];
  announcements: Announcement[];
}

export interface Register {
  instructional: boolean;
  submitted: boolean;
  submitted_at: string | null;
  editable: boolean;
  students: (RosterStudent & { status: AttendanceStatus | null; remark: string | null })[];
}

export interface RegisterSubmission {
  section_id: string;
  day: string;
  period_no: number;
  reason: string | null;
  records: { student_id: string; status: AttendanceStatus }[];
}

export interface AssessmentRow {
  id: string;
  name: string;
  kind: string;
  max_marks: string;
  held_on: string;
  is_published: boolean;
  entered: number;
  enrolled: number;
  complete: boolean;
}

export interface MarksSheet {
  assessment: AssessmentRow;
  students: (RosterStudent & { marks_obtained: string | null; is_absent: boolean; remarks: string | null })[];
}

export interface AssessmentInput {
  section_id: string;
  subject_id: string;
  name: string;
  kind: string;
  max_marks: string;
  held_on: string;
}

export interface Topic {
  id: string;
  sequence: number;
  title: string;
  status: TopicStatus;
  planned_periods: number;
  periods_used: number;
  started_on: string | null;
  completed_on: string | null;
}

export interface TopicList {
  topics: Topic[];
  completed: number;
  total: number;
  note: string;
}

export interface LessonPrompt {
  timetable_entry_id: string;
  period_no: number;
  section_id: string;
  section: string;
  subject_id: string;
  subject: string;
  current_topic: Topic | null;
  next_topic: Topic | null;
}

export type TopicActionName = "start" | "continue" | "keep_pending" | "complete" | "reopen";

export interface TopicFeedbackSummary {
  topic_id: string;
  title: string;
  status: string;
  responses: number;
  average_understanding: number;
  needs_support: string[];
  comments: { comment: string; understanding: number; student: string | null }[];
}

export interface ClassOverview {
  section: string;
  subjects: string[];
  students: {
    student_id: string;
    name: string;
    roll_no: number;
    attendance_percent: number | null;
    absences: number;
    subject_averages: Record<string, number>;
    overall_percent: number | null;
  }[];
  follow_up: { student_id: string; name: string; roll_no: number; reasons: string[] }[];
  missing: { registers: string[]; assessments: { assessment_id: string; name: string; missing: number }[] };
  thresholds: { attendance: number; performance: number };
}

const pair = (a: Pick<Assignment, "section_id" | "subject_id">) => ({ section_id: a.section_id, subject_id: a.subject_id });

export const teacherApi = {
  dashboard: () => queryDef<TeacherDashboard>("/teacher/dashboard"),
  timetable: () => queryDef<TimetableData>("/teacher/timetable"),
  assignments: () => queryDef<Assignment[]>("/teacher/assignments"),
  sectionStudents: (sectionId: string) => queryDef<RosterStudent[]>(`/teacher/sections/${sectionId}/students`),
  register: (sectionId: string, day: string, periodNo: number) =>
    queryDef<Register>(withQuery("/teacher/attendance", { section_id: sectionId, day, period_no: periodNo })),
  assessments: (a: Assignment) => queryDef<AssessmentRow[]>(withQuery("/teacher/assessments", pair(a))),
  marks: (assessmentId: string) => queryDef<MarksSheet>(`/teacher/assessments/${assessmentId}/marks`),
  topics: (a: Assignment) => queryDef<TopicList>(withQuery("/teacher/topics", pair(a))),
  lessonPrompts: () => queryDef<LessonPrompt[]>("/teacher/lesson-prompts"),
  topicFeedback: (a: Assignment) => queryDef<TopicFeedbackSummary[]>(withQuery("/teacher/topic-feedback", pair(a))),
  threads: () => queryDef<MessageThread[]>("/teacher/messages"),
  thread: (id: string) => queryDef<MessageThreadDetail>(`/teacher/messages/${id}`),
  complaints: () => queryDef<Complaint[]>("/teacher/complaints"),
  classOverview: (sectionId: string) => queryDef<ClassOverview>(`/teacher/class/${sectionId}`),

  saveRegister: (body: RegisterSubmission) => http.put<{ corrections: number; action: string }>("/teacher/attendance", body),
  createAssessment: (body: AssessmentInput) => http.post<AssessmentRow>("/teacher/assessments", body),
  saveMarks: ({
    assessmentId,
    ...body
  }: {
    assessmentId: string;
    reason: string | null;
    marks: { student_id: string; is_absent: boolean; marks_obtained: string | null }[];
  }) => http.put<{ saved: number; corrections: number }>(`/teacher/assessments/${assessmentId}/marks`, body),
  addTopic: (body: { section_id: string; subject_id: string; title: string; planned_periods: number }) =>
    http.post<Topic>("/teacher/topics", body),
  topicAction: ({
    topicId,
    ...body
  }: {
    topicId: string;
    action: TopicActionName;
    confirm?: boolean;
    start_next?: boolean;
    notes?: string | null;
    timetable_entry_id?: string | null;
  }) => http.post<{ topic: Topic; started_next: Topic | null }>(`/teacher/topics/${topicId}/action`, body),
  reply: ({ threadId, body }: { threadId: string; body: string }) =>
    http.post<{ ok: boolean }>(`/teacher/messages/${threadId}/reply`, { body }),
  updateComplaint: ({ id, ...body }: { id: string } & ComplaintStatusUpdate) =>
    http.post<{ ok: boolean }>(`/teacher/complaints/${id}/update`, body),
};
