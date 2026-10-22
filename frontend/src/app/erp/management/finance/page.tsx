import type { Metadata } from "next";
import { FinanceView } from "@/features/common/finance-view";

export const metadata: Metadata = { title: "Fees & Finance" };

export default function Page() {
  return <FinanceView />;
}
