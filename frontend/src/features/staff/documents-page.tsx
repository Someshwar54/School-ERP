"use client";

import { Alert, Card, DataState, PageHeader } from "@/components/ui";
import { DocumentTable } from "@/features/common/document-table";
import { useApiQuery } from "@/lib/api/query";
import { staffApi } from "@/services/staff";

export function StaffDocumentsPage() {
  const state = useApiQuery(staffApi.documents());
  return (
    <>
      <PageHeader title="Documents" />
      <Alert tone="warning" className="mb-4">
        File storage is not connected in this prototype; only document records are shown.
      </Alert>
      <Card padded={false}>
        <DataState state={state}>{(rows) => <DocumentTable documents={rows} />}</DataState>
      </Card>
    </>
  );
}
