"use client";

import { useState, type FormEvent } from "react";
import { Alert, Button, Field, Input, Select, Textarea } from "@/components/ui";
import { ADMISSION_GRADES } from "@/domain/options";
import { hasErrors, validateEnquiry } from "@/domain/validation";
import { useApiMutation } from "@/lib/api/query";
import { publicApi, type EnquiryInput } from "@/services/public-site";

export function EnquiryForm() {
  const [errors, setErrors] = useState<ReturnType<typeof validateEnquiry>>({});
  const [result, setResult] = useState<{ message: string; notifications?: string } | null>(null);
  const submitEnquiry = useApiMutation(publicApi.createEnquiry);

  async function onSubmit(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    const form = ev.currentTarget;
    const values = Object.fromEntries(new FormData(form).entries()) as unknown as EnquiryInput;
    const errs = validateEnquiry(values);
    setErrors(errs);
    setResult(null);
    submitEnquiry.reset();
    if (hasErrors(errs)) return;
    const res = await submitEnquiry.run(values).catch(() => null);
    if (res) {
      setResult(res);
      form.reset();
    }
  }

  return (
    <form noValidate onSubmit={onSubmit} className="space-y-4" aria-label="Admission enquiry form">
      {result && (
        <Alert tone="success" title="Enquiry received">
          {result.message}
          {result.notifications && <p className="mt-1 text-xs opacity-80">{result.notifications}</p>}
        </Alert>
      )}
      {submitEnquiry.error && (
        <Alert tone="error" title="Could not send enquiry">
          {submitEnquiry.error.message}
        </Alert>
      )}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Parent / guardian name" required error={errors.parent_name}>
          {(p) => <Input name="parent_name" autoComplete="name" {...p} />}
        </Field>
        <Field label="Email" required error={errors.email}>
          {(p) => <Input name="email" type="email" autoComplete="email" {...p} />}
        </Field>
        <Field label="Mobile number" required error={errors.phone} hint="10 digits, without +91">
          {(p) => <Input name="phone" inputMode="numeric" autoComplete="tel-national" maxLength={10} {...p} />}
        </Field>
        <Field label="Grade sought" required error={errors.grade_sought}>
          {(p) => (
            <Select name="grade_sought" defaultValue="" {...p}>
              <option value="" disabled>
                Select a grade
              </option>
              {ADMISSION_GRADES.map((g) => (
                <option key={g}>{g}</option>
              ))}
            </Select>
          )}
        </Field>
      </div>
      <Field label="Message (optional)">{(p) => <Textarea name="message" maxLength={2000} {...p} />}</Field>
      {/* Honeypot: hidden from people, often filled by bots. */}
      <div aria-hidden className="hidden">
        <label>
          Website <input name="website" tabIndex={-1} autoComplete="off" />
        </label>
      </div>
      <Button type="submit" loading={submitEnquiry.pending}>
        Send enquiry
      </Button>
    </form>
  );
}
