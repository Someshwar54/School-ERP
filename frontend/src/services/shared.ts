/** Endpoints shared by every signed-in account, plus DTOs reused across workspaces. */
import { withQuery, type Page } from "@/lib/api/client";
import { queryDef } from "@/lib/api/query-def";

export interface Announcement {
  id: string;
  title: string;
  body: string;
  audience: string;
  is_pinned: boolean;
  published_at: string;
  section_specific: boolean;
}

export interface SchoolEvent {
  id: string;
  title: string;
  description: string;
  starts_at: string;
  ends_at: string;
  location: string;
  is_past: boolean;
}

export interface DocumentRecord {
  id: string;
  title: string;
  category: string;
  scope: string;
  available: boolean;
  created_at: string;
}

export interface TimetableData {
  periods: { period_no: number; label: string; starts_at: string; ends_at: string }[];
  entries: {
    id: string;
    day_of_week: number;
    period_no: number;
    subject: string;
    subject_id: string;
    section: string;
    section_id: string;
    teacher: string | null;
    room: string | null;
  }[];
  today_day_of_week: number;
}

export interface Complaint {
  id: string;
  reference_no: string;
  category: string;
  subject: string;
  description: string;
  is_confidential: boolean;
  status: string;
  section: string | null;
  assigned_to: string | null;
  student: string | null;
  created_at: string;
  updates: { note: string; new_status: string | null; author: string; created_at: string }[];
}

export interface ComplaintStatusUpdate {
  note: string;
  status: string | null;
}

export interface MessageThread {
  id: string;
  subject: string;
  staff_name: string | null;
  student_name: string | null;
  last_message_at: string;
}

export interface MessageThreadDetail extends MessageThread {
  messages: { id: string; body: string; sender: string | null; created_at: string; mine: boolean }[];
}

export interface Leave {
  id: string;
  staff_name?: string | null;
  leave_type: string;
  starts_on: string;
  ends_on: string;
  days: number;
  reason: string;
  status: string;
  decision_comment: string | null;
  is_own?: boolean;
}

export const sharedApi = {
  announcements: (page: number, pageSize = 10) => queryDef<Page<Announcement>>(withQuery("/announcements", { page, page_size: pageSize })),
  events: () => queryDef<SchoolEvent[]>("/events"),
};
