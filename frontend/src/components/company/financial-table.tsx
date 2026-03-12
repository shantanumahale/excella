"use client";

import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { formatLargeNumber, formatDate } from "@/lib/formatters";
import type { FinancialStatement } from "@/lib/types";
import { cn } from "@/lib/utils";

interface FinancialTableProps {
  statements: FinancialStatement[];
  statementType: string;
}

/** Human-readable labels for common financial statement keys */
const INCOME_LABELS: Record<string, string> = {
  revenue: "Revenue",
  cost_of_revenue: "Cost of Revenue",
  gross_profit: "Gross Profit",
  operating_expenses: "Operating Expenses",
  research_and_development: "Research & Development",
  selling_general_and_admin: "SG&A",
  operating_income: "Operating Income",
  interest_expense: "Interest Expense",
  income_before_tax: "Income Before Tax",
  income_tax_expense: "Income Tax Expense",
  net_income: "Net Income",
  eps_basic: "EPS (Basic)",
  eps_diluted: "EPS (Diluted)",
  shares_outstanding_basic: "Shares Outstanding (Basic)",
  shares_outstanding_diluted: "Shares Outstanding (Diluted)",
  ebitda: "EBITDA",
  depreciation_and_amortization: "Depreciation & Amortization",
  stock_based_compensation: "Stock-Based Compensation",
  other_income_expense: "Other Income / Expense",
  total_other_income_expense: "Total Other Income",
};

const BALANCE_LABELS: Record<string, string> = {
  total_assets: "Total Assets",
  total_current_assets: "Total Current Assets",
  cash_and_equivalents: "Cash & Equivalents",
  short_term_investments: "Short-Term Investments",
  accounts_receivable: "Accounts Receivable",
  inventory: "Inventory",
  other_current_assets: "Other Current Assets",
  total_non_current_assets: "Total Non-Current Assets",
  property_plant_equipment: "PP&E (Net)",
  goodwill: "Goodwill",
  intangible_assets: "Intangible Assets",
  total_liabilities: "Total Liabilities",
  total_current_liabilities: "Total Current Liabilities",
  accounts_payable: "Accounts Payable",
  short_term_debt: "Short-Term Debt",
  total_non_current_liabilities: "Total Non-Current Liabilities",
  long_term_debt: "Long-Term Debt",
  total_equity: "Total Equity",
  retained_earnings: "Retained Earnings",
  common_stock: "Common Stock",
  total_liabilities_and_equity: "Total Liabilities & Equity",
};

const CASHFLOW_LABELS: Record<string, string> = {
  operating_cash_flow: "Operating Cash Flow",
  net_income_cf: "Net Income",
  depreciation_amortization: "Depreciation & Amortization",
  stock_based_compensation_cf: "Stock-Based Compensation",
  change_in_working_capital: "Change in Working Capital",
  accounts_receivable_change: "Change in Receivables",
  inventory_change: "Change in Inventory",
  accounts_payable_change: "Change in Payables",
  investing_cash_flow: "Investing Cash Flow",
  capital_expenditures: "Capital Expenditures",
  acquisitions: "Acquisitions",
  purchases_of_investments: "Purchases of Investments",
  sales_of_investments: "Sales of Investments",
  financing_cash_flow: "Financing Cash Flow",
  debt_issued: "Debt Issued",
  debt_repaid: "Debt Repaid",
  shares_issued: "Shares Issued",
  shares_repurchased: "Shares Repurchased",
  dividends_paid: "Dividends Paid",
  net_change_in_cash: "Net Change in Cash",
  free_cash_flow: "Free Cash Flow",
};

function getLabelMap(statementType: string): Record<string, string> {
  switch (statementType) {
    case "income":
      return INCOME_LABELS;
    case "balance":
      return BALANCE_LABELS;
    case "cashflow":
      return CASHFLOW_LABELS;
    default:
      return {};
  }
}

function humanizeKey(key: string): string {
  return key
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function FinancialTable({ statements, statementType }: FinancialTableProps) {
  if (!statements || statements.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-8 text-center">
        No financial data available.
      </p>
    );
  }

  // Sort statements by period_end descending (most recent first)
  const sorted = [...statements].sort(
    (a, b) => new Date(b.period_end).getTime() - new Date(a.period_end).getTime()
  );

  // Collect all unique keys from the data JSONB across all periods
  const allKeys = new Set<string>();
  sorted.forEach((s) => {
    if (s.data) {
      Object.keys(s.data).forEach((k) => allKeys.add(k));
    }
  });

  const labelMap = getLabelMap(statementType);
  const knownOrder = Object.keys(labelMap);
  const keyList: string[] = [];

  // Add known keys in order first
  for (const k of knownOrder) {
    if (allKeys.has(k)) {
      keyList.push(k);
      allKeys.delete(k);
    }
  }
  // Add remaining unknown keys sorted alphabetically
  const remaining = Array.from(allKeys).sort();
  keyList.push(...remaining);

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="sticky left-0 z-10 bg-card min-w-[200px]">
              Line Item
            </TableHead>
            {sorted.map((s) => (
              <TableHead key={s.id} className="text-right min-w-[120px] whitespace-nowrap">
                <div className="text-xs">
                  {formatDate(s.period_end)}
                </div>
                <div className="text-[10px] text-muted-foreground">
                  {s.fiscal_period} {s.fiscal_year}
                </div>
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {keyList.map((key) => (
            <TableRow key={key}>
              <TableCell className="sticky left-0 z-10 bg-card font-medium text-sm whitespace-nowrap">
                {labelMap[key] ?? humanizeKey(key)}
              </TableCell>
              {sorted.map((s) => {
                const val = s.data?.[key];
                const isNumber = typeof val === "number";
                return (
                  <TableCell
                    key={s.id}
                    className={cn(
                      "text-right tabular-nums text-sm",
                      isNumber && val < 0 && "text-loss"
                    )}
                  >
                    {isNumber
                      ? formatLargeNumber(val)
                      : val !== null && val !== undefined
                        ? String(val)
                        : "--"}
                  </TableCell>
                );
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
