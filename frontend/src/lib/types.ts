// ---------------------------------------------------------------------------
// Company
// ---------------------------------------------------------------------------

export interface Company {
  id: number;
  cik: string;
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  exchange: string | null;
  fiscal_year_end: string | null;
  website: string | null;
  description: string | null;
  market_cap: number | null;
  employees: number | null;
  created_at: string;
  updated_at: string;
  latest_metrics: DerivedMetrics | null;
}

export interface CompanyListItem {
  id: number;
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  exchange: string | null;
}

// ---------------------------------------------------------------------------
// Pagination
// ---------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  total: number;
  offset: number;
  limit: number;
  data: T[];
}

// ---------------------------------------------------------------------------
// Financial Statements
// ---------------------------------------------------------------------------

export interface FinancialStatement {
  id: number;
  company_id: number;
  statement_type: string;
  period_start: string;
  period_end: string;
  fiscal_period: string;
  fiscal_year: number;
  data: Record<string, any>;
}

// ---------------------------------------------------------------------------
// Derived Metrics — all 12 JSONB categories
// ---------------------------------------------------------------------------

export interface DerivedMetrics {
  period_end: string;
  fiscal_period: string;
  profitability: Record<string, number | null>;
  liquidity: Record<string, number | null>;
  leverage: Record<string, number | null>;
  efficiency: Record<string, number | null>;
  cashflow: Record<string, number | null>;
  growth: Record<string, number | null>;
  dupont: Record<string, number | null>;
  valuation: Record<string, number | null>;
  quality: Record<string, number | null>;
  forensic: Record<string, number | null>;
  shareholder: Record<string, number | null>;
  per_share: Record<string, number | null>;
}

// ---------------------------------------------------------------------------
// Prices
// ---------------------------------------------------------------------------

export interface PriceBar {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adj_close: number;
  volume: number;
}

export interface PriceReturns {
  ticker: string;
  date: string;
  returns: {
    "1d": number | null;
    "5d": number | null;
    "21d": number | null;
    "63d": number | null;
    "126d": number | null;
    "252d": number | null;
  };
}

// ---------------------------------------------------------------------------
// FRED / Macro
// ---------------------------------------------------------------------------

export interface FredSeries {
  id: number;
  series_id: string;
  title: string;
  frequency: string;
  units: string;
  seasonal_adjustment: string;
  notes: string | null;
  last_updated: string;
}

export interface FredObservation {
  time: string;
  value: number | null;
}

// ---------------------------------------------------------------------------
// Screener
// ---------------------------------------------------------------------------

export interface ScreenerFilter {
  metric: string;
  operator: string;
  value: number;
}

export interface ScreenerRequest {
  filters: ScreenerFilter[];
  sort_by?: string;
  sort_order?: "asc" | "desc";
  offset?: number;
  limit?: number;
}

export interface ScreenerResult {
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  period_end: string;
  fiscal_period: string;
  metrics: Record<string, number | null>;
}

// ---------------------------------------------------------------------------
// Metric Catalogue
// ---------------------------------------------------------------------------

export type MetricCatalogue = Record<string, string[]>;
