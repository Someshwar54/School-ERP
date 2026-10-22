"use client";

import { useState } from "react";
import { Alert, Button, Card, Checkbox, DataState, Field, Input, PageHeader } from "@/components/ui";
import { school } from "@/config/school";
import { titleCase } from "@/lib/format";
import { ERP_MODULES } from "@/domain/options";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { managementApi, type SchoolSettings } from "@/services/management";

export function SchoolConfigPage() {
  const state = useApiQuery(managementApi.config());
  return (
    <>
      <PageHeader
        title="School configuration"
        description="Operational settings are validated on the server and every change is audited. Branding and public website content are managed in the deployment configuration."
      />
      <DataState state={state}>
        {(d) => <ConfigForm key={d.version} initial={d.settings} version={d.version} canManage={d.can_manage} />}
      </DataState>
    </>
  );
}

function ConfigForm({ initial, version, canManage }: { initial: SchoolSettings; version: number; canManage: boolean }) {
  const [s, setS] = useState<SchoolSettings>(initial);
  // Settings change menus (enabled modules) and thresholds, so refresh the session and management data.
  const save = useApiMutation(managementApi.saveConfig, { invalidates: ["/management", "/auth/me"] });
  const [saved, setSaved] = useState(false);

  async function onSave() {
    setSaved(false);
    if (await save.run({ version, settings: s }).catch(() => null)) setSaved(true);
  }
  const disabled = !canManage;
  return (
    <div className="space-y-6">
      {!canManage && <Alert tone="info">Read-only: your role can view but not change configuration.</Alert>}
      {saved && !save.error && <Alert tone="success">Configuration saved.</Alert>}
      {save.error && <Alert tone="error">{save.error.message}</Alert>}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Enabled ERP modules">
          <div className="grid grid-cols-2 gap-2">
            {ERP_MODULES.map((m) => (
              <Checkbox
                key={m}
                label={titleCase(m)}
                disabled={disabled}
                checked={s.enabled_modules.includes(m)}
                onChange={(e) =>
                  setS({ ...s, enabled_modules: e.target.checked ? [...s.enabled_modules, m] : s.enabled_modules.filter((x) => x !== m) })
                }
              />
            ))}
          </div>
        </Card>
        <Card title="Terminology">
          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(s.terminology).map(([k, v]) => (
              <Field key={k} label={titleCase(k)}>
                {(p) => (
                  <Input
                    disabled={disabled}
                    value={v}
                    onChange={(e) => setS({ ...s, terminology: { ...s.terminology, [k]: e.target.value } })}
                    {...p}
                  />
                )}
              </Field>
            ))}
          </div>
        </Card>
        <Card title="Academic thresholds">
          <div className="grid gap-3 sm:grid-cols-3">
            {(["pass_percent", "attendance_alert_percent", "low_performance_percent"] as const).map((k) => (
              <Field key={k} label={titleCase(k)}>
                {(p) => (
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    disabled={disabled}
                    value={s.academic[k]}
                    onChange={(e) => setS({ ...s, academic: { ...s.academic, [k]: Number(e.target.value) } })}
                    {...p}
                  />
                )}
              </Field>
            ))}
          </div>
          <p className="mt-3 text-sm text-muted">
            Grade scale: {s.academic.grade_scale.map((g) => `${g.grade} ≥ ${g.min_percent}%`).join(" · ")}
          </p>
        </Card>
        <Card title="Attendance policy">
          <div className="space-y-2">
            <Checkbox
              label="Count late arrivals as attended"
              disabled={disabled}
              checked={s.attendance.count_late_as_present}
              onChange={(e) => setS({ ...s, attendance: { ...s.attendance, count_late_as_present: e.target.checked } })}
            />
            <Checkbox
              label="Exclude approved leave / excused absence from the percentage"
              disabled={disabled}
              checked={s.attendance.exclude_authorised_absence}
              onChange={(e) => setS({ ...s, attendance: { ...s.attendance, exclude_authorised_absence: e.target.checked } })}
            />
            <Checkbox
              label="Enable period-wise attendance"
              disabled={disabled}
              checked={s.attendance.period_attendance_enabled}
              onChange={(e) => setS({ ...s, attendance: { ...s.attendance, period_attendance_enabled: e.target.checked } })}
            />
            <Field label="Correction window (days)">
              {(p) => (
                <Input
                  type="number"
                  min={0}
                  max={60}
                  className="w-28"
                  disabled={disabled}
                  value={s.attendance.correction_window_days}
                  onChange={(e) => setS({ ...s, attendance: { ...s.attendance, correction_window_days: Number(e.target.value) } })}
                  {...p}
                />
              )}
            </Field>
          </div>
        </Card>
        <Card title="Branding (deployment configuration)">
          <dl className="grid grid-cols-[9rem_1fr] gap-y-2 text-sm">
            <dt className="text-muted">School name</dt>
            <dd>{school.name}</dd>
            <dt className="text-muted">Colours</dt>
            <dd className="flex items-center gap-2">
              {[school.theme.primary, school.theme.secondary].map((c) => (
                <span key={c} className="inline-flex items-center gap-1">
                  <span className="size-4 rounded border border-line" style={{ background: c }} />
                  {c}
                </span>
              ))}
            </dd>
            <dt className="text-muted">Regional</dt>
            <dd>
              {s.regional.locale} · {s.regional.currency} · {s.regional.timezone}
            </dd>
          </dl>
          <p className="mt-3 text-xs text-muted">
            Logo, colours and public content are set in <code>frontend/src/config/schools/</code> and validated at build time.
          </p>
        </Card>
      </div>
      {canManage && (
        <Button onClick={() => void onSave()} loading={save.pending}>
          Save configuration
        </Button>
      )}
    </div>
  );
}
