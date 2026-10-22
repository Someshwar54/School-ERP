/** Finance endpoints. Amounts are exact decimal strings end to end. */
import { http, withQuery } from "@/lib/api/client";
import { queryDef } from "@/lib/api/query-def";

export interface FinanceSummary {
  billed_net: string;
  concessions: string;
  collected: string;
  refunded: string;
  outstanding: string;
  overdue_invoices: number;
  overdue_amount: string;
  collection_rate_percent: number | null;
  monthly_collection: { month: string; amount: string }[];
}

export interface InvoiceRow {
  id: string;
  invoice_no: string;
  student_code: string;
  student_name: string;
  term: string | null;
  due_on: string;
  status: string;
  net: string;
  paid: string;
  balance: string;
}

export interface PaymentInput {
  invoice_id: string;
  amount: string;
  method: string;
  reference: string | null;
  paid_on: string;
}

export const financeApi = {
  summary: () => queryDef<FinanceSummary>("/finance/summary"),
  invoices: (q: string, status: string, page: number) =>
    queryDef<{ items: InvoiceRow[]; total: number; page: number; page_size: number }>(
      withQuery("/finance/invoices", { q, status, page, page_size: 15 }),
    ),
  recordPayment: (body: PaymentInput) => http.post<{ receipt_no: string; amount: string; new_balance: string }>("/finance/payments", body),
};
