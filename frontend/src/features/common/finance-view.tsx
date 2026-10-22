"use client";

import { useState, type FormEvent } from "react";
import { barTrace, ChartPanel } from "@/components/charts/chart";
import { Alert, Badge, Button, Card, DataState, Dialog, Field, Input, PageHeader, Pager, Select, Stat, Table, Td } from "@/components/ui";
import { INVOICE_TONE } from "@/domain/status";
import { validatePaymentAmount } from "@/domain/validation";
import { useSession } from "@/features/auth/use-session";
import { useTodayISO } from "@/hooks/use-today";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { formatDate, formatMoney, titleCase } from "@/lib/format";
import { financeApi, type FinanceSummary, type InvoiceRow } from "@/services/finance";

const PAYMENT_METHODS = ["upi", "cash", "card", "bank_transfer", "cheque"];
const INVOICE_STATUSES = ["overdue", "unpaid", "partially_paid", "paid"];

export function FinanceSummaryBlock({ s }: { s: FinanceSummary }) {
  const months = s.monthly_collection.map((m) => formatDate(`${m.month}-01`, { month: "short", year: "2-digit" }));
  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Billed (net of concessions)" value={formatMoney(s.billed_net)} hint={`Concessions ${formatMoney(s.concessions)}`} />
        <Stat
          label="Collected"
          value={formatMoney(s.collected)}
          hint={s.collection_rate_percent !== null ? `${s.collection_rate_percent}% of billed (after refunds)` : undefined}
        />
        <Stat label="Outstanding" value={formatMoney(s.outstanding)} tone="warning" hint={`Refunded ${formatMoney(s.refunded)}`} />
        <Stat
          label="Overdue"
          value={formatMoney(s.overdue_amount)}
          tone={s.overdue_invoices ? "warning" : "good"}
          hint={`${s.overdue_invoices} invoice(s) past due`}
        />
      </div>
      <Card title="Fee collection by month">
        <ChartPanel
          label="Fee collection by month"
          data={[
            barTrace(
              months,
              s.monthly_collection.map((m) => Number(m.amount)),
              "Collected",
              { hovertemplate: "%{x}<br>Collected: ₹%{y:,.0f}<extra></extra>" },
            ),
          ]}
          layout={{ yaxis: { tickprefix: "₹", tickformat: ",.0f" } }}
          height={240}
          headers={["Month", "Collected"]}
          rows={s.monthly_collection.map((m) => [m.month, formatMoney(m.amount)])}
        />
        <p className="mt-2 text-xs text-muted">
          All figures are derived from the invoice and payment ledger; there are no separately editable balances.
        </p>
      </Card>
    </div>
  );
}

/** Fees module for finance staff and management. What each role sees is decided by the backend. */
export function FinanceView() {
  const { can } = useSession();
  const summary = useApiQuery(financeApi.summary());
  return (
    <>
      <PageHeader
        title="Fees and finance"
        description="Online payments, bank reconciliation and accounting exports are not connected in this prototype."
      />
      <div className="space-y-6">
        <DataState state={summary}>{(s) => <FinanceSummaryBlock s={s} />}</DataState>
        {can("finance.view") ? (
          <Invoices canRecord={can("finance.record_payment")} />
        ) : (
          <Alert tone="info">Your role can see aggregated fee figures only. Individual student invoices require finance permission.</Alert>
        )}
      </div>
    </>
  );
}

function Invoices({ canRecord }: { canRecord: boolean }) {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [paying, setPaying] = useState<InvoiceRow | null>(null);
  const state = useApiQuery(financeApi.invoices(q, status, page));
  return (
    <Card
      title="Invoices"
      padded={false}
      action={
        <div className="flex flex-wrap gap-2">
          <Input
            className="w-52"
            placeholder="Student ID, name or invoice"
            aria-label="Search invoices"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
          />
          <Select
            className="w-40"
            aria-label="Filter by status"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All statuses</option>
            {INVOICE_STATUSES.map((s) => (
              <option key={s} value={s}>
                {titleCase(s)}
              </option>
            ))}
          </Select>
        </div>
      }
    >
      <DataState state={state}>
        {(d) => (
          <>
            <Table
              headers={["Invoice", "Student", "Term", "Due", "Net", "Paid", "Balance", "Status", ""]}
              empty={d.items.length === 0}
              caption="Invoices"
            >
              {d.items.map((i) => (
                <tr key={i.id}>
                  <Td className="font-medium">{i.invoice_no}</Td>
                  <Td>
                    {i.student_name}
                    <span className="block text-xs text-muted">{i.student_code}</span>
                  </Td>
                  <Td>{i.term}</Td>
                  <Td>{formatDate(i.due_on)}</Td>
                  <Td>{formatMoney(i.net)}</Td>
                  <Td>{formatMoney(i.paid)}</Td>
                  <Td className="font-medium">{formatMoney(i.balance)}</Td>
                  <Td>
                    <Badge tone={INVOICE_TONE[i.status]}>{titleCase(i.status)}</Badge>
                  </Td>
                  <Td>
                    {canRecord && Number(i.balance) > 0 && (
                      <Button size="sm" variant="secondary" onClick={() => setPaying(i)}>
                        Record payment
                      </Button>
                    )}
                  </Td>
                </tr>
              ))}
            </Table>
            <div className="px-4 pb-3">
              <Pager page={d.page} pageSize={d.page_size} total={d.total} onPage={setPage} />
            </div>
          </>
        )}
      </DataState>
      {paying && <RecordPaymentDialog invoice={paying} onClose={() => setPaying(null)} />}
    </Card>
  );
}

function RecordPaymentDialog({ invoice, onClose }: { invoice: InvoiceRow; onClose: () => void }) {
  const today = useTodayISO();
  const [form, setForm] = useState({ amount: invoice.balance, method: "upi", reference: "", paid_on: "" });
  const [localError, setLocalError] = useState<string | null>(null);
  // Invalidate every finance read so the summary, invoice list and ledgers all refresh.
  const record = useApiMutation(financeApi.recordPayment, { invalidates: ["/finance"] });

  async function submit(e?: FormEvent) {
    e?.preventDefault();
    const amountError = validatePaymentAmount(form.amount, invoice.balance);
    setLocalError(amountError);
    if (amountError) return;
    const ok = await record
      .run({
        invoice_id: invoice.id,
        amount: form.amount,
        method: form.method,
        reference: form.reference || null,
        paid_on: form.paid_on || today || "",
      })
      .catch(() => null);
    if (ok) onClose();
  }

  const error = localError ?? record.error?.message;
  return (
    <Dialog
      open
      title={`Record payment · ${invoice.invoice_no}`}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button loading={record.pending} onClick={() => void submit()}>
            Record payment
          </Button>
        </>
      }
    >
      <p className="text-muted">
        {invoice.student_name} · outstanding {formatMoney(invoice.balance)}
      </p>
      {error && <Alert tone="error">{error}</Alert>}
      <form onSubmit={submit} className="space-y-3">
        <Field label="Amount (₹)">
          {(p) => <Input inputMode="decimal" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} {...p} />}
        </Field>
        <Field label="Method">
          {(p) => (
            <Select value={form.method} onChange={(e) => setForm({ ...form, method: e.target.value })} {...p}>
              {PAYMENT_METHODS.map((m) => (
                <option key={m} value={m}>
                  {titleCase(m)}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Reference (optional)">
          {(p) => <Input value={form.reference} maxLength={64} onChange={(e) => setForm({ ...form, reference: e.target.value })} {...p} />}
        </Field>
        <Field label="Payment date">
          {(p) => (
            <Input
              type="date"
              value={form.paid_on || today || ""}
              max={today ?? undefined}
              onChange={(e) => setForm({ ...form, paid_on: e.target.value })}
              {...p}
            />
          )}
        </Field>
      </form>
      <p className="text-xs text-muted">This records a payment already received at the school. It does not charge anyone.</p>
    </Dialog>
  );
}
