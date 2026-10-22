"use client";

import { Spinner } from "@/components/ui";
import { useSession } from "@/features/auth/use-session";
import { TeacherDashboard } from "@/features/teacher/dashboard";
import { StaffDashboard } from "./staff-dashboard";

/** Staff workspace home. Teachers (decided by the backend from their assignments) get the teacher dashboard. */
export function StaffHomePage() {
  const { me } = useSession();
  if (!me) return <Spinner />;
  return me.workspace.is_teacher ? <TeacherDashboard /> : <StaffDashboard />;
}
