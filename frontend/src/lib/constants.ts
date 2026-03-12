// ---------------------------------------------------------------------------
// Metric categories with display metadata
// ---------------------------------------------------------------------------

export const METRIC_CATEGORIES = [
  { id: "profitability", label: "Profitability", color: "emerald" },
  { id: "liquidity", label: "Liquidity", color: "sky" },
  { id: "leverage", label: "Leverage", color: "rose" },
  { id: "efficiency", label: "Efficiency", color: "amber" },
  { id: "cashflow", label: "Cash Flow", color: "violet" },
  { id: "growth", label: "Growth", color: "lime" },
  { id: "dupont", label: "DuPont Analysis", color: "cyan" },
  { id: "valuation", label: "Valuation", color: "orange" },
  { id: "quality", label: "Quality", color: "teal" },
  { id: "forensic", label: "Forensic", color: "red" },
  { id: "shareholder", label: "Shareholder", color: "indigo" },
  { id: "per_share", label: "Per Share", color: "fuchsia" },
] as const;

// ---------------------------------------------------------------------------
// Category → Tailwind color class mapping
// ---------------------------------------------------------------------------

export const CATEGORY_COLORS: Record<string, string> = {
  profitability: "bg-emerald-500",
  liquidity: "bg-sky-500",
  leverage: "bg-rose-500",
  efficiency: "bg-amber-500",
  cashflow: "bg-violet-500",
  growth: "bg-lime-500",
  dupont: "bg-cyan-500",
  valuation: "bg-orange-500",
  quality: "bg-teal-500",
  forensic: "bg-red-500",
  shareholder: "bg-indigo-500",
  per_share: "bg-fuchsia-500",
};

// ---------------------------------------------------------------------------
// Default screener table columns
// ---------------------------------------------------------------------------

export const DEFAULT_SCREENER_COLUMNS: string[] = [
  "ticker",
  "name",
  "sector",
  "industry",
  "market_cap",
  "pe_ratio",
  "price_to_book",
  "ev_to_ebitda",
  "gross_margin",
  "operating_margin",
  "net_margin",
  "return_on_equity",
  "return_on_invested_capital",
  "debt_to_equity",
  "current_ratio",
  "free_cash_flow_to_firm",
  "revenue_growth",
  "net_income_growth",
  "dividend_yield",
  "altman_z_score",
  "piotroski_f_score",
];
