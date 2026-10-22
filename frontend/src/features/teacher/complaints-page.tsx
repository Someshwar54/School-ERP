"use client";

import { DataState, PageHeader } from "@/components/ui";
import { ComplaintList } from "@/features/common/complaint-list";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { teacherApi } from "@/services/teacher";

export function TeacherComplaintsPage() {
  const state = useApiQuery(teacherApi.complaints());
  const update = useApiMutation(teacherApi.updateComplaint, { invalidates: ["/teacher/complaints", "/teacher/dashboard"] });
  return (
    <>
      <PageHeader
        title="Assigned complaints"
        description="Non-confidential complaints routed to you as class teacher. Confidential matters are handled by management and never appear here."
      />
      <DataState state={state}>{(items) => <ComplaintList items={items} update={update} />}</DataState>
    </>
  );
}
