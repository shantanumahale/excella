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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  valuation_models: any;
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
  value: number | number[];
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
// Valuation Models
// ---------------------------------------------------------------------------

export interface ValuationModelSummary {
  consensus_value: number | null;
  margin_of_safety: number | null;
  model_count: number;
  model_values?: { model: string; value: number }[];
  range_low?: number;
  range_high?: number;
}

export interface DCFResult {
  intrinsic_value_per_share: number;
  enterprise_value: number;
  equity_value: number;
  projected_fcff: number[];
  terminal_value: number;
  pv_fcff: number[];
  pv_terminal: number;
  projection_years: number;
  method: string;
}

export interface CompsResult {
  peer_count: number;
  peers: {
    ticker: string;
    name: string;
    multiples: Record<string, number | null>;
  }[];
  multiples: Record<string, number | null>;
  implied_values: Record<string, number | null>;
}

export interface ValuationResult {
  ticker: string;
  period_end?: string;
  beta?: {
    beta: number;
    r_squared: number | null;
    alpha: number | null;
    lookback_days: number;
    data_points: number;
    is_fallback: boolean;
  };
  risk_free_rate?: number;
  wacc?: {
    wacc: number;
    cost_of_equity?: number;
    cost_of_debt_after_tax?: number;
    equity_weight?: number;
    debt_weight?: number;
  };
  models: {
    dcf: DCFResult | null;
    ddm: {
      intrinsic_value_per_share: number;
      model_type: string;
      dividend_yield_implied: number | null;
    } | null;
    comps: CompsResult | null;
    residual_income: {
      intrinsic_value_per_share: number;
      current_bvps: number;
      excess_returns: number[];
      pv_excess_returns: number[];
      pv_terminal: number;
      projection_years: number;
    } | null;
  };
  summary: ValuationModelSummary;
}

export interface DCFParams {
  growth_rate?: number;
  terminal_growth: number;
  wacc?: number;
  projection_years: number;
  terminal_method: "perpetuity" | "exit_multiple";
  exit_multiple?: number;
  risk_free_rate?: number;
}

export interface SensitivityResult {
  ticker: string;
  base_wacc: number;
  wacc_range: number[];
  growth_range: number[];
  matrix: {
    wacc: number;
    values: Record<string, number | null>;
  }[];
}

export interface ValuationHistoryPoint {
  period_end: string;
  intrinsic_value: number | null;
  price: number | null;
  margin_of_safety: number | null;
  model_count: number | null;
}

// ---------------------------------------------------------------------------
// Metric Catalogue
// ---------------------------------------------------------------------------

export type MetricCatalogue = Record<string, string[]>;
