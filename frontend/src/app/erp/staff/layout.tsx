import { WorkspaceShell } from "@/features/workspace/workspace-shell";

export default function StaffLayout({ children }: { children: React.ReactNode }) {
  return <WorkspaceShell kind="staff">{children}</WorkspaceShell>;
}
