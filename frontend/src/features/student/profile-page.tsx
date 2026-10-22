"use client";

import { Badge, Card, DataState, PageHeader } from "@/components/ui";
import { formatDate, titleCase } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { studentApi } from "@/services/student";

export function StudentProfilePage() {
  const state = useApiQuery(studentApi.profile());
  return (
    <DataState state={state}>
      {(p) => (
        <>
          <PageHeader title="My profile" description={p.note} />
          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="Student details">
              <dl className="grid grid-cols-[10rem_1fr] gap-y-2 text-sm">
                {[
                  ["Name", p.name],
                  ["Student ID", p.student_code],
                  ["Admission no.", p.admission_no],
                  ["Class", p.section ?? "—"],
                  ["Roll no.", p.roll_no ?? "—"],
                  ["Date of birth", formatDate(p.date_of_birth)],
                  ["Gender", titleCase(p.gender)],
                  ["Blood group", p.blood_group ?? "—"],
                  ["Admitted on", formatDate(p.admission_date)],
                ].map(([k, v]) => (
                  <div key={String(k)} className="contents">
                    <dt className="text-muted">{k}</dt>
                    <dd className="font-medium">{v}</dd>
                  </div>
                ))}
              </dl>
            </Card>
            <Card title="Contact and guardians">
              <dl className="grid grid-cols-[10rem_1fr] gap-y-2 text-sm">
                <dt className="text-muted">Registered phone</dt>
                <dd className="font-medium">{p.phone_masked}</dd>
                <dt className="text-muted">Email</dt>
                <dd className="font-medium">{p.email ?? "—"}</dd>
                <dt className="text-muted">Address</dt>
                <dd className="font-medium">{p.address ?? "—"}</dd>
              </dl>
              <h3 className="mt-5 text-sm font-semibold">Guardians</h3>
              <ul className="mt-2 space-y-2 text-sm">
                {p.guardians.map((g) => (
                  <li key={g.name} className="flex flex-wrap items-center gap-2">
                    <span className="font-medium">{g.name}</span>
                    <span className="text-muted">({titleCase(g.relationship)})</span>
                    <Badge tone={g.verification === "verified" ? "success" : "warning"}>{titleCase(g.verification)}</Badge>
                    {g.is_primary && <Badge tone="info">Primary</Badge>}
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-muted">
                Parent/guardian portal accounts are planned and will require a verified relationship.
              </p>
            </Card>
          </div>
        </>
      )}
    </DataState>
  );
}
