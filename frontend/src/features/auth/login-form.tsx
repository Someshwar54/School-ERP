"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Alert, Button, Field, Input, PasswordInput } from "@/components/ui";
import { hasErrors, validateLogin } from "@/domain/validation";
import { useApiMutation } from "@/lib/api/query";
import { authApi, type Portal } from "@/services/auth";

const COPY: Record<Portal, { idLabel: string; idHint: string; placeholder: string }> = {
  student: { idLabel: "Student ID", idHint: "Your school-issued Student ID, e.g. STU0123.", placeholder: "STU0000" },
  staff: { idLabel: "Staff ID", idHint: "Your school-issued Staff ID, e.g. EMP1001.", placeholder: "EMP0000" },
  director: { idLabel: "Director ID", idHint: "Your management ID issued by the school.", placeholder: "DIR000" },
};

export function LoginForm({ portal, demoNote }: { portal: Portal; demoNote?: string }) {
  const router = useRouter();
  const client = useQueryClient();
  const copy = COPY[portal];
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<ReturnType<typeof validateLogin>>({});
  const login = useApiMutation(authApi.login);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const errs = validateLogin({ loginId, password }, copy.idLabel);
    setErrors(errs);
    login.reset();
    if (hasErrors(errs)) return;
    try {
      const res = await login.run({ portal, login_id: loginId.trim(), password });
      client.clear(); // never reuse cached data from a previous account
      router.replace(res.home);
    } catch {
      setPassword("");
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-5" aria-label={`${copy.idLabel} sign-in form`}>
      {login.error && (
        <Alert tone="error" title="Sign-in failed">
          {login.error.message}
        </Alert>
      )}
      <Field label={copy.idLabel} required error={errors.loginId} hint={copy.idHint}>
        {(p) => (
          <Input
            name="login_id"
            autoComplete="username"
            autoCapitalize="characters"
            spellCheck={false}
            placeholder={copy.placeholder}
            value={loginId}
            onChange={(e) => setLoginId(e.target.value)}
            {...p}
          />
        )}
      </Field>
      <Field label="Password" required error={errors.password}>
        {(p) => (
          <PasswordInput
            name="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            {...p}
          />
        )}
      </Field>
      <Button type="submit" size="lg" className="w-full" loading={login.pending}>
        {login.pending ? "Signing in…" : "Sign in"}
      </Button>
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
        <Link href="/erp/recovery" className="font-medium text-brand hover:underline">
          Forgot password?
        </Link>
        <Link href="/erp" className="text-muted hover:text-ink hover:underline">
          Other sign-in options
        </Link>
      </div>
      {demoNote && <p className="rounded-brand bg-surface p-3 text-xs text-muted">{demoNote}</p>}
    </form>
  );
}
