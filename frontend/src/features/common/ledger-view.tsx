/** Student fee ledger: invoices with lines, payments and refunds. Read-only; balances come from the server. */
import { Badge, Card, Stat, Table, Td } from "@/components/ui";
import { INVOICE_TONE } from "@/domain/status";
import { formatDate, formatMoney, titleCase } from "@/lib/format";
import type { Ledger } from "@/services/student";

export function LedgerView({ d }: { d: Ledger }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Total billed (net)" value={formatMoney(d.totals.billed)} hint={`Concessions ${formatMoney(d.totals.concessions)}`} />
        <Stat label="Paid" value={formatMoney(d.totals.paid)} />
        <Stat label="Refunded" value={formatMoney(d.totals.refunded)} />
        <Stat
          label="Outstanding"
          value={formatMoney(d.totals.outstanding)}
          tone={Number(d.totals.outstanding) > 0 ? "warning" : "good"}
          hint={d.next_due ? `Next due ${formatDate(d.next_due.due_on)}` : undefined}
        />
      </div>
      <Card title="Invoices">
        <div className="space-y-5">
          {d.invoices.map((inv) => (
            <article key={inv.id} className="rounded-brand border border-line">
              <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line bg-surface px-4 py-2.5">
                <div>
                  <p className="text-sm font-semibold">
                    {inv.invoice_no} · {inv.term}
                  </p>
                  <p className="text-xs text-muted">
                    Issued {formatDate(inv.issued_on)} · Due {formatDate(inv.due_on)}
                  </p>
                </div>
                <Badge tone={INVOICE_TONE[inv.status]}>{titleCase(inv.status)}</Badge>
              </header>
              <ul className="divide-y divide-line px-4 text-sm">
                {inv.lines.map((l, i) => (
                  <li key={i} className="flex justify-between py-1.5">
                    <span className={l.line_type === "concession" ? "text-emerald-800" : undefined}>{l.description}</span>
                    <span>{l.line_type === "concession" ? `− ${formatMoney(l.amount)}` : formatMoney(l.amount)}</span>
                  </li>
                ))}
              </ul>
              <footer className="flex flex-wrap justify-end gap-x-6 gap-y-1 border-t border-line px-4 py-2 text-sm">
                <span>
                  Net <strong>{formatMoney(inv.net)}</strong>
                </span>
                <span>
                  Paid <strong>{formatMoney(inv.paid)}</strong>
                </span>
                <span>
                  Balance <strong>{formatMoney(inv.balance)}</strong>
                </span>
              </footer>
            </article>
          ))}
        </div>
      </Card>
      <Card title="Payments and receipts" padded={false}>
        <Table headers={["Receipt", "Date", "Method", "Amount", "Applied to"]} empty={d.payments.length === 0} caption="Payments">
          {d.payments.map((p) => (
            <tr key={p.id}>
              <Td className="font-medium">{p.receipt_no}</Td>
              <Td>{formatDate(p.paid_on)}</Td>
              <Td>{titleCase(p.method)}</Td>
              <Td>{formatMoney(p.amount)}</Td>
              <Td className="text-muted">{p.allocations.map((a) => `${a.invoice_no}: ${formatMoney(a.amount)}`).join(", ")}</Td>
            </tr>
          ))}
        </Table>
      </Card>
      {d.refunds.length > 0 && (
        <Card title="Refunds" padded={false}>
          <Table headers={["Receipt", "Date", "Amount", "Reason"]} caption="Refunds">
            {d.refunds.map((r, i) => (
              <tr key={i}>
                <Td>{r.receipt_no}</Td>
                <Td>{formatDate(r.refunded_on)}</Td>
                <Td>{formatMoney(r.amount)}</Td>
                <Td className="text-muted">{r.reason}</Td>
              </tr>
            ))}
          </Table>
        </Card>
      )}
    </div>
  );
}
