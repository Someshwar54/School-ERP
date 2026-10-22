import {
  BadgeIndianRupee,
  BarChart3,
  BookMarked,
  BookOpen,
  Briefcase,
  Bus,
  CalendarCheck,
  CalendarClock,
  CalendarDays,
  ClipboardCheck,
  ClipboardList,
  FileText,
  Gauge,
  GraduationCap,
  HeartHandshake,
  LayoutDashboard,
  Library,
  ListChecks,
  Megaphone,
  MessageSquare,
  MessageSquareWarning,
  NotebookPen,
  Settings,
  ShieldCheck,
  Star,
  User,
  UserCog,
  Users,
  type LucideIcon,
} from "lucide-react";
import type { WorkspaceKind } from "@/services/auth";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

/** Labels and routes for module keys. WHICH modules appear is decided by the backend (/auth/me). */
const defs: Record<WorkspaceKind, Record<string, NavItem>> = {
  student: {
    dashboard: { label: "Dashboard", href: "/erp/student", icon: LayoutDashboard },
    profile: { label: "My Profile", href: "/erp/student/profile", icon: User },
    attendance: { label: "Attendance", href: "/erp/student/attendance", icon: CalendarCheck },
    performance: { label: "Academic Performance", href: "/erp/student/performance", icon: BarChart3 },
    results: { label: "Examinations & Results", href: "/erp/student/results", icon: GraduationCap },
    timetable: { label: "Timetable", href: "/erp/student/timetable", icon: CalendarClock },
    fees: { label: "Fees & Payments", href: "/erp/student/fees", icon: BadgeIndianRupee },
    announcements: { label: "Announcements", href: "/erp/student/announcements", icon: Megaphone },
    events: { label: "Events", href: "/erp/student/events", icon: CalendarDays },
    documents: { label: "Documents & Report Cards", href: "/erp/student/documents", icon: FileText },
    messages: { label: "Teacher Communication", href: "/erp/student/messages", icon: MessageSquare },
    complaints: { label: "Complaints & Requests", href: "/erp/student/complaints", icon: MessageSquareWarning },
    feedback: { label: "Feedback", href: "/erp/student/feedback", icon: Star },
    settings: { label: "Account Settings", href: "/erp/student/settings", icon: Settings },
  },
  staff: {
    dashboard: { label: "Dashboard", href: "/erp/staff", icon: LayoutDashboard },
    timetable: { label: "Timetable", href: "/erp/staff/timetable", icon: CalendarClock },
    classes: { label: "Classes & Subjects", href: "/erp/staff/classes", icon: BookOpen },
    attendance: { label: "Student Attendance", href: "/erp/staff/attendance", icon: CalendarCheck },
    marks: { label: "Assessments & Marks", href: "/erp/staff/marks", icon: NotebookPen },
    topics: { label: "Lesson Progression", href: "/erp/staff/topics", icon: ListChecks },
    support: { label: "Student Support", href: "/erp/staff/support", icon: HeartHandshake },
    complaints: { label: "Assigned Complaints", href: "/erp/staff/complaints", icon: MessageSquareWarning },
    class: { label: "My Class (Class Teacher)", href: "/erp/staff/class", icon: Users },
    "my-attendance": { label: "My Attendance", href: "/erp/staff/my-attendance", icon: ClipboardCheck },
    leave: { label: "Leave Requests", href: "/erp/staff/leave", icon: CalendarDays },
    duties: { label: "Assigned Duties", href: "/erp/staff/duties", icon: ClipboardList },
    announcements: { label: "Announcements", href: "/erp/staff/announcements", icon: Megaphone },
    documents: { label: "Documents", href: "/erp/staff/documents", icon: FileText },
    finance: { label: "Fees & Finance", href: "/erp/staff/finance", icon: BadgeIndianRupee },
    hr: { label: "HR", href: "/erp/staff/hr", icon: Briefcase },
    library: { label: "Library", href: "/erp/staff/library", icon: Library },
    transport: { label: "Transport", href: "/erp/staff/transport", icon: Bus },
    profile: { label: "Profile & Settings", href: "/erp/staff/profile", icon: UserCog },
  },
  management: {
    overview: { label: "Executive Overview", href: "/erp/management", icon: Gauge },
    academics: { label: "Academic Performance", href: "/erp/management/academics", icon: GraduationCap },
    "staff-performance": { label: "Teacher & Staff Performance", href: "/erp/management/staff-performance", icon: BookMarked },
    attendance: { label: "Student & Staff Attendance", href: "/erp/management/attendance", icon: CalendarCheck },
    finance: { label: "Fees & Finance", href: "/erp/management/finance", icon: BadgeIndianRupee },
    hr: { label: "Payroll & HR", href: "/erp/management/hr", icon: Briefcase },
    complaints: { label: "Complaints & Feedback", href: "/erp/management/complaints", icon: MessageSquareWarning },
    reports: { label: "Reports & Analytics", href: "/erp/management/reports", icon: BarChart3 },
    approvals: { label: "Approvals & Audit", href: "/erp/management/approvals", icon: ShieldCheck },
    config: { label: "School Configuration", href: "/erp/management/config", icon: Settings },
    settings: { label: "Account Settings", href: "/erp/management/settings", icon: UserCog },
  },
};

export function navFor(kind: WorkspaceKind, modules: string[]): NavItem[] {
  return modules.map((m) => defs[kind][m]).filter((x): x is NavItem => Boolean(x));
}
