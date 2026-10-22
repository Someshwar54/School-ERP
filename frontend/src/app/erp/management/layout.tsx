import { WorkspaceShell } from "@/features/workspace/workspace-shell";

export default function ManagementLayout({ children }: { children: React.ReactNode }) {
  return <WorkspaceShell kind="management">{children}</WorkspaceShell>;
}
