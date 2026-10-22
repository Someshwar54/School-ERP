import { WorkspaceShell } from "@/features/workspace/workspace-shell";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return <WorkspaceShell kind="student">{children}</WorkspaceShell>;
}
