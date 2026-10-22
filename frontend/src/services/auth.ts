/** Authentication endpoints and the signed-in user's workspace description. */
import { http } from "@/lib/api/client";
import { queryDef } from "@/lib/api/query-def";

export type WorkspaceKind = "student" | "staff" | "management";
export type Portal = "student" | "staff" | "director";

export interface Me {
  user: { login_id: string; display_name: string; account_type: WorkspaceKind | "guardian"; must_change_password: boolean };
  school: { name: string; slug: string };
  workspace: {
    kind: WorkspaceKind;
    home: string;
    modules: string[];
    roles: string[];
    permissions: string[];
    is_teacher?: boolean | null;
    teaching_assignments?: number | null;
    class_teacher_of?: { section_id: string; section: string }[] | null;
  };
  session: { expires_at: string; idle_minutes: number };
  demo_mode: boolean;
}

export const LOGIN_PATH: Record<WorkspaceKind, string> = {
  student: "/erp/login/student",
  staff: "/erp/login/staff",
  management: "/erp/login/director",
};

export const authApi = {
  me: () => queryDef<Me>("/auth/me"),
  login: (body: { portal: Portal; login_id: string; password: string }) =>
    http.post<{ ok: boolean; home: string; must_change_password: boolean }>("/auth/login", body),
  logout: () => http.post<{ ok: boolean }>("/auth/logout"),
  changePassword: (body: { current_password: string; new_password: string }) =>
    http.post<{ ok: boolean; other_sessions_signed_out: number }>("/auth/change-password", body),
  revokeOtherSessions: () => http.post<{ ok: boolean; signed_out: number }>("/auth/sessions/revoke-others"),
};
