"use client";

import { useState, type FormEvent } from "react";
import { Alert, Button, Card, Field, PageHeader, PasswordInput } from "@/components/ui";
import { hasErrors, validatePasswordChange } from "@/domain/validation";
import { useSession } from "@/features/auth/use-session";
import { useApiMutation } from "@/lib/api/query";
import { formatDateTime } from "@/lib/format";
import { authApi } from "@/services/auth";

export function AccountSettings() {
  const { me } = useSession();
  const [form, setForm] = useState({ current: "", next: "", confirm: "" });
  const [errors, setErrors] = useState<ReturnType<typeof validatePasswordChange>>({});
  const [notice, setNotice] = useState<string | null>(null);
  const changePassword = useApiMutation(authApi.changePassword, { invalidates: ["/auth/me"] });
  const revokeOthers = useApiMutation(authApi.revokeOtherSessions);
  const error = changePassword.error ?? revokeOthers.error;

  async function submit(e: FormEvent) {
    e.preventDefault();
    const errs = validatePasswordChange(form);
    setErrors(errs);
    setNotice(null);
    if (hasErrors(errs)) return;
    const r = await changePassword.run({ current_password: form.current, new_password: form.next }).catch(() => null);
    if (r) {
      setForm({ current: "", next: "", confirm: "" });
      setNotice(`Password changed. ${r.other_sessions_signed_out} other session(s) were signed out.`);
    }
  }

  async function signOutOthers() {
    setNotice(null);
    const r = await revokeOthers.run(undefined).catch(() => null);
    if (r) setNotice(`${r.signed_out} other session(s) signed out.`);
  }

  return (
    <>
      <PageHeader title="Account settings" description={me ? `${me.user.display_name} · ${me.user.login_id}` : undefined} />
      {notice && (
        <Alert tone="success" className="mb-4">
          {notice}
        </Alert>
      )}
      {error && (
        <Alert tone="error" className="mb-4">
          {error.message}
        </Alert>
      )}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Change password">
          <form onSubmit={submit} noValidate className="space-y-4">
            <Field label="Current password" required error={errors.current}>
              {(p) => (
                <PasswordInput
                  autoComplete="current-password"
                  value={form.current}
                  onChange={(e) => setForm({ ...form, current: e.target.value })}
                  {...p}
                />
              )}
            </Field>
            <Field
              label="New password"
              required
              error={errors.next}
              hint="At least 10 characters with letters and numbers. Do not use your ID or phone number."
            >
              {(p) => (
                <PasswordInput
                  autoComplete="new-password"
                  value={form.next}
                  onChange={(e) => setForm({ ...form, next: e.target.value })}
                  {...p}
                />
              )}
            </Field>
            <Field label="Confirm new password" required error={errors.confirm}>
              {(p) => (
                <PasswordInput
                  autoComplete="new-password"
                  value={form.confirm}
                  onChange={(e) => setForm({ ...form, confirm: e.target.value })}
                  {...p}
                />
              )}
            </Field>
            <Button type="submit" loading={changePassword.pending}>
              Update password
            </Button>
          </form>
        </Card>
        <Card title="Sessions and security">
          <div className="space-y-3 text-sm text-muted">
            {me && (
              <p>
                This session expires on {formatDateTime(me.session.expires_at)} and after {me.session.idle_minutes} minutes of inactivity.
              </p>
            )}
            <p>Signing out other sessions ends access on any other device or browser using your account.</p>
            <Button variant="secondary" loading={revokeOthers.pending} onClick={() => void signOutOthers()}>
              Sign out other sessions
            </Button>
          </div>
        </Card>
      </div>
    </>
  );
}
