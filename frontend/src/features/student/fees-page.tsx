"use client";

import { LedgerView } from "@/features/common/ledger-view";
import { Alert, DataState, PageHeader } from "@/components/ui";
import { useApiQuery } from "@/lib/api/query";
import { studentApi } from "@/services/student";

export function StudentFeesPage() {
  const state = useApiQuery(studentApi.fees());
  return (
    <>
      <PageHeader
        title="Fees and payments"
        description="Balances are calculated from the school's fee ledger. Records cannot be edited here."
      />
      <Alert tone="info" className="mb-5">
        Online payment is not connected in this prototype. Please pay at the school accounts office.
      </Alert>
      <DataState state={state}>{(d) => <LedgerView d={d} />}</DataState>
    </>
  );
}
