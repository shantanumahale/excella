// ---------------------------------------------------------------------------
// Comprehensive metric metadata for all 142 derived metrics across 12 categories
// ---------------------------------------------------------------------------

import type { FormatType } from "./formatters";

export interface MetricMeta {
  key: string;
  label: string;
  category: string;
  format: FormatType;
  description: string;
}

// ---------------------------------------------------------------------------
// Master list
// ---------------------------------------------------------------------------

export const METRIC_METADATA: MetricMeta[] = [
  // =========================================================================
  // PROFITABILITY (16)
  // =========================================================================
  { key: "gross_margin", label: "Gross Margin", category: "profitability", format: "percent", description: "(Revenue − COGS) ÷ Revenue" },
  { key: "operating_margin", label: "Operating Margin", category: "profitability", format: "percent", description: "Operating Income ÷ Revenue" },
  { key: "net_margin", label: "Net Margin", category: "profitability", format: "percent", description: "Net Income ÷ Revenue" },
  { key: "ebitda_margin", label: "EBITDA Margin", category: "profitability", format: "percent", description: "EBITDA ÷ Revenue" },
  { key: "ebit_margin", label: "EBIT Margin", category: "profitability", format: "percent", description: "EBIT ÷ Revenue" },
  { key: "return_on_assets", label: "Return on Assets", category: "profitability", format: "percent", description: "Net Income ÷ Total Assets" },
  { key: "return_on_equity", label: "Return on Equity", category: "profitability", format: "percent", description: "Net Income ÷ Shareholders' Equity" },
  { key: "return_on_capital_employed", label: "Return on Capital Employed", category: "profitability", format: "percent", description: "EBIT ÷ (Total Assets − Current Liabilities)" },
  { key: "return_on_invested_capital", label: "Return on Invested Capital", category: "profitability", format: "percent", description: "NOPAT ÷ Invested Capital" },
  { key: "effective_tax_rate", label: "Effective Tax Rate", category: "profitability", format: "percent", description: "Income Tax ÷ Pre-Tax Income" },
  { key: "nopat", label: "NOPAT", category: "profitability", format: "currency", description: "Operating Income × (1 − Tax Rate)" },
  { key: "invested_capital", label: "Invested Capital", category: "profitability", format: "currency", description: "Total Debt + Equity − Cash" },
  { key: "capital_employed", label: "Capital Employed", category: "profitability", format: "currency", description: "Total Assets − Current Liabilities" },
  { key: "rd_intensity", label: "R&D Intensity", category: "profitability", format: "percent", description: "R&D Expense ÷ Revenue" },
  { key: "sga_ratio", label: "SG&A Ratio", category: "profitability", format: "percent", description: "SG&A Expense ÷ Revenue" },
  { key: "sbc_pct_revenue", label: "SBC % Revenue", category: "profitability", format: "percent", description: "Stock-Based Compensation ÷ Revenue" },

  // =========================================================================
  // LIQUIDITY (10)
  // =========================================================================
  { key: "current_ratio", label: "Current Ratio", category: "liquidity", format: "ratio", description: "Current Assets ÷ Current Liabilities" },
  { key: "quick_ratio", label: "Quick Ratio", category: "liquidity", format: "ratio", description: "(Current Assets − Inventory) ÷ Current Liabilities" },
  { key: "cash_ratio", label: "Cash Ratio", category: "liquidity", format: "ratio", description: "Cash & Equivalents ÷ Current Liabilities" },
  { key: "net_working_capital", label: "Net Working Capital", category: "liquidity", format: "currency", description: "Current Assets − Current Liabilities" },
  { key: "nwc_pct_revenue", label: "NWC % Revenue", category: "liquidity", format: "percent", description: "Net Working Capital ÷ Revenue" },
  { key: "days_inventory_outstanding", label: "Days Inventory Outstanding", category: "liquidity", format: "number", description: "Inventory ÷ (COGS ÷ 365)" },
  { key: "days_sales_outstanding", label: "Days Sales Outstanding", category: "liquidity", format: "number", description: "Accounts Receivable ÷ (Revenue ÷ 365)" },
  { key: "days_payable_outstanding", label: "Days Payable Outstanding", category: "liquidity", format: "number", description: "Accounts Payable ÷ (COGS ÷ 365)" },
  { key: "cash_conversion_cycle", label: "Cash Conversion Cycle", category: "liquidity", format: "number", description: "DIO + DSO − DPO" },
  { key: "defensive_interval", label: "Defensive Interval", category: "liquidity", format: "number", description: "Liquid Assets ÷ Daily Operating Expenses" },

  // =========================================================================
  // LEVERAGE (10)
  // =========================================================================
  { key: "total_debt", label: "Total Debt", category: "leverage", format: "currency", description: "Short-Term Debt + Long-Term Debt" },
  { key: "net_debt", label: "Net Debt", category: "leverage", format: "currency", description: "Total Debt − Cash & Equivalents" },
  { key: "debt_to_equity", label: "Debt-to-Equity", category: "leverage", format: "ratio", description: "Total Debt ÷ Shareholders' Equity" },
  { key: "debt_to_assets", label: "Debt-to-Assets", category: "leverage", format: "ratio", description: "Total Debt ÷ Total Assets" },
  { key: "debt_to_ebitda", label: "Debt-to-EBITDA", category: "leverage", format: "ratio", description: "Net Debt ÷ EBITDA" },
  { key: "interest_coverage", label: "Interest Coverage", category: "leverage", format: "ratio", description: "EBIT ÷ Interest Expense" },
  { key: "equity_multiplier", label: "Equity Multiplier", category: "leverage", format: "ratio", description: "Total Assets ÷ Shareholders' Equity" },
  { key: "debt_to_capital", label: "Debt-to-Capital", category: "leverage", format: "ratio", description: "Total Debt ÷ (Total Debt + Equity)" },
  { key: "long_term_debt_to_equity", label: "LT Debt-to-Equity", category: "leverage", format: "ratio", description: "Long-Term Debt ÷ Shareholders' Equity" },
  { key: "financial_leverage_ratio", label: "Financial Leverage Ratio", category: "leverage", format: "ratio", description: "Total Assets ÷ Total Equity" },

  // =========================================================================
  // EFFICIENCY (10)
  // =========================================================================
  { key: "asset_turnover", label: "Asset Turnover", category: "efficiency", format: "ratio", description: "Revenue ÷ Total Assets" },
  { key: "fixed_asset_turnover", label: "Fixed Asset Turnover", category: "efficiency", format: "ratio", description: "Revenue ÷ Net PP&E" },
  { key: "inventory_turnover", label: "Inventory Turnover", category: "efficiency", format: "ratio", description: "COGS ÷ Inventory" },
  { key: "receivables_turnover", label: "Receivables Turnover", category: "efficiency", format: "ratio", description: "Revenue ÷ Accounts Receivable" },
  { key: "payables_turnover", label: "Payables Turnover", category: "efficiency", format: "ratio", description: "COGS ÷ Accounts Payable" },
  { key: "equity_turnover", label: "Equity Turnover", category: "efficiency", format: "ratio", description: "Revenue ÷ Shareholders' Equity" },
  { key: "capital_expenditure_to_revenue", label: "CapEx-to-Revenue", category: "efficiency", format: "percent", description: "|CapEx| ÷ Revenue" },
  { key: "capex_to_depreciation", label: "CapEx-to-Depreciation", category: "efficiency", format: "ratio", description: "|CapEx| ÷ D&A" },
  { key: "operating_cycle", label: "Operating Cycle", category: "efficiency", format: "number", description: "DIO + DSO" },
  { key: "cash_cycle", label: "Cash Cycle", category: "efficiency", format: "number", description: "Operating Cycle − DPO" },

  // =========================================================================
  // CASH FLOW (11)
  // =========================================================================
  { key: "free_cash_flow_to_firm", label: "FCFF", category: "cashflow", format: "currency", description: "OCF − |CapEx| + Interest × (1 − Tax Rate)" },
  { key: "free_cash_flow_to_firm_simplified", label: "FCFF (Simplified)", category: "cashflow", format: "currency", description: "OCF − |CapEx|" },
  { key: "free_cash_flow_to_equity", label: "FCFE", category: "cashflow", format: "currency", description: "OCF − |CapEx| + Net Borrowing" },
  { key: "net_borrowing", label: "Net Borrowing", category: "cashflow", format: "currency", description: "Debt Issued − Debt Repaid" },
  { key: "operating_cash_flow_margin", label: "OCF Margin", category: "cashflow", format: "percent", description: "Operating Cash Flow ÷ Revenue" },
  { key: "cash_flow_to_net_income", label: "Cash Flow / Net Income", category: "cashflow", format: "ratio", description: "OCF ÷ Net Income" },
  { key: "capex_to_operating_cash_flow", label: "CapEx / OCF", category: "cashflow", format: "percent", description: "|CapEx| ÷ OCF" },
  { key: "cash_return_on_invested_capital", label: "Cash ROIC", category: "cashflow", format: "percent", description: "FCFF ÷ Invested Capital" },
  { key: "reinvestment_rate", label: "Reinvestment Rate", category: "cashflow", format: "percent", description: "|CapEx| ÷ NOPAT" },
  { key: "capex_to_depreciation_cf", label: "CapEx / Depreciation", category: "cashflow", format: "ratio", description: "|CapEx| ÷ D&A" },
  { key: "nopat_cf", label: "NOPAT", category: "cashflow", format: "currency", description: "Operating Income × (1 − Tax Rate)" },

  // =========================================================================
  // GROWTH (15)
  // =========================================================================
  { key: "revenue_growth", label: "Revenue Growth", category: "growth", format: "percent", description: "(Revenue − Prior Revenue) ÷ |Prior Revenue|" },
  { key: "gross_profit_growth", label: "Gross Profit Growth", category: "growth", format: "percent", description: "(Gross Profit − Prior) ÷ |Prior|" },
  { key: "operating_income_growth", label: "Operating Income Growth", category: "growth", format: "percent", description: "(Operating Income − Prior) ÷ |Prior|" },
  { key: "ebitda_growth", label: "EBITDA Growth", category: "growth", format: "percent", description: "(EBITDA − Prior) ÷ |Prior|" },
  { key: "net_income_growth", label: "Net Income Growth", category: "growth", format: "percent", description: "(Net Income − Prior) ÷ |Prior|" },
  { key: "eps_growth", label: "EPS Growth", category: "growth", format: "percent", description: "(EPS − Prior EPS) ÷ |Prior EPS|" },
  { key: "operating_cash_flow_growth", label: "OCF Growth", category: "growth", format: "percent", description: "(OCF − Prior OCF) ÷ |Prior OCF|" },
  { key: "free_cash_flow_growth", label: "FCF Growth", category: "growth", format: "percent", description: "(FCF − Prior FCF) ÷ |Prior FCF|" },
  { key: "total_assets_growth", label: "Total Assets Growth", category: "growth", format: "percent", description: "(Total Assets − Prior) ÷ |Prior|" },
  { key: "equity_growth", label: "Equity Growth", category: "growth", format: "percent", description: "(Equity − Prior Equity) ÷ |Prior Equity|" },
  { key: "dividend_growth", label: "Dividend Growth", category: "growth", format: "percent", description: "(|Dividends| − |Prior|) ÷ |Prior|" },
  { key: "sustainable_growth_rate", label: "Sustainable Growth Rate", category: "growth", format: "percent", description: "ROE × Retention Ratio" },
  { key: "is_acquisition_period", label: "Acquisition Period", category: "growth", format: "boolean", description: "Acquisitions ≠ 0" },
  { key: "acquisition_to_revenue", label: "Acquisition / Revenue", category: "growth", format: "percent", description: "|Acquisitions| ÷ Revenue" },
  { key: "reinvestment_rate_growth", label: "Reinvestment Rate", category: "growth", format: "percent", description: "(Reinvestment Rate − Prior) ÷ |Prior|" },

  // =========================================================================
  // DUPONT (9)
  // =========================================================================
  { key: "net_margin_dupont", label: "Net Margin", category: "dupont", format: "percent", description: "Net Income ÷ Revenue" },
  { key: "asset_turnover_dupont", label: "Asset Turnover", category: "dupont", format: "ratio", description: "Revenue ÷ Total Assets" },
  { key: "equity_multiplier_dupont", label: "Equity Multiplier", category: "dupont", format: "ratio", description: "Total Assets ÷ Equity" },
  { key: "roe_3factor", label: "ROE (3-Factor)", category: "dupont", format: "percent", description: "Net Margin × Asset Turnover × Equity Multiplier" },
  { key: "tax_burden", label: "Tax Burden", category: "dupont", format: "ratio", description: "Net Income ÷ Pre-Tax Income" },
  { key: "interest_burden", label: "Interest Burden", category: "dupont", format: "ratio", description: "Pre-Tax Income ÷ EBIT" },
  { key: "operating_profit_margin", label: "Operating Profit Margin", category: "dupont", format: "percent", description: "EBIT ÷ Revenue" },
  { key: "roe_5factor", label: "ROE (5-Factor)", category: "dupont", format: "percent", description: "Tax Burden × Interest Burden × OPM × Asset Turnover × Equity Multiplier" },
  { key: "tax_efficiency", label: "Tax Efficiency", category: "dupont", format: "percent", description: "Net Income ÷ Pre-Tax Income" },
  { key: "interest_efficiency", label: "Interest Efficiency", category: "dupont", format: "percent", description: "Pre-Tax Income ÷ EBIT" },

  // =========================================================================
  // VALUATION (18)
  // =========================================================================
  { key: "market_cap", label: "Market Cap", category: "valuation", format: "currency", description: "Share Price × Shares Outstanding" },
  { key: "enterprise_value", label: "Enterprise Value", category: "valuation", format: "currency", description: "Market Cap + Total Debt − Cash + Minority Interest" },
  { key: "pe_ratio", label: "P/E Ratio", category: "valuation", format: "ratio", description: "Share Price ÷ EPS" },
  { key: "price_to_book", label: "Price-to-Book", category: "valuation", format: "ratio", description: "Market Cap ÷ Total Equity" },
  { key: "price_to_sales", label: "Price-to-Sales", category: "valuation", format: "ratio", description: "Market Cap ÷ Revenue" },
  { key: "price_to_cash_flow", label: "Price-to-Cash Flow", category: "valuation", format: "ratio", description: "Market Cap ÷ OCF" },
  { key: "ev_to_ebitda", label: "EV/EBITDA", category: "valuation", format: "ratio", description: "Enterprise Value ÷ EBITDA" },
  { key: "ev_to_ebit", label: "EV/EBIT", category: "valuation", format: "ratio", description: "Enterprise Value ÷ EBIT" },
  { key: "ev_to_revenue", label: "EV/Revenue", category: "valuation", format: "ratio", description: "Enterprise Value ÷ Revenue" },
  { key: "ev_to_fcf", label: "EV/FCF", category: "valuation", format: "ratio", description: "Enterprise Value ÷ FCF" },
  { key: "earnings_yield", label: "Earnings Yield", category: "valuation", format: "percent", description: "EPS ÷ Share Price" },
  { key: "fcf_yield", label: "FCF Yield", category: "valuation", format: "percent", description: "FCF per Share ÷ Share Price" },
  { key: "dividend_yield", label: "Dividend Yield", category: "valuation", format: "percent", description: "Dividends per Share ÷ Share Price" },
  { key: "peg_ratio", label: "PEG Ratio", category: "valuation", format: "ratio", description: "P/E Ratio ÷ EPS Growth %" },
  { key: "book_value_per_share", label: "Book Value / Share", category: "valuation", format: "currency", description: "Total Equity ÷ Shares Outstanding" },
  { key: "tangible_book_value_per_share", label: "Tangible BV / Share", category: "valuation", format: "currency", description: "(Equity − Goodwill − Intangibles) ÷ Shares Outstanding" },
  { key: "revenue_per_share", label: "Revenue / Share", category: "valuation", format: "currency", description: "Revenue ÷ Shares Outstanding" },
  { key: "graham_number", label: "Graham Number", category: "valuation", format: "currency", description: "√(22.5 × EPS × BVPS)" },

  // =========================================================================
  // QUALITY (10)
  // =========================================================================
  { key: "accruals_ratio", label: "Accruals Ratio", category: "quality", format: "ratio", description: "(Net Income − OCF) ÷ Total Assets" },
  { key: "sloan_ratio", label: "Sloan Ratio", category: "quality", format: "ratio", description: "(Net Income − OCF) ÷ Total Assets" },
  { key: "cash_flow_to_earnings", label: "Cash Flow / Earnings", category: "quality", format: "ratio", description: "OCF ÷ Net Income" },
  { key: "earnings_quality_score", label: "Earnings Quality Score", category: "quality", format: "score", description: "1 if OCF > Net Income, else 0" },
  { key: "revenue_vs_receivables_divergence", label: "Revenue vs Receivables Divergence", category: "quality", format: "percent", description: "Revenue Growth − Receivables Growth" },
  { key: "net_income_vs_ocf_divergence", label: "Net Income vs OCF Divergence", category: "quality", format: "percent", description: "Net Income Growth − OCF Growth" },
  { key: "capex_consistency", label: "CapEx Consistency", category: "quality", format: "ratio", description: "|CapEx| ÷ Revenue" },
  { key: "organic_revenue_flag", label: "Organic Revenue Flag", category: "quality", format: "boolean", description: "Acquisitions = 0" },
  { key: "sga_efficiency", label: "SG&A Efficiency", category: "quality", format: "ratio", description: "Revenue Growth − SG&A Growth" },
  { key: "depreciation_to_capex", label: "Depreciation / CapEx", category: "quality", format: "ratio", description: "D&A ÷ |CapEx|" },

  // =========================================================================
  // FORENSIC (10)
  // =========================================================================
  { key: "altman_z_score", label: "Altman Z-Score", category: "forensic", format: "score", description: "1.2×X₁ + 1.4×X₂ + 3.3×X₃ + 0.6×X₄ + 1.0×X₅" },
  { key: "altman_z_components", label: "Altman Z Components", category: "forensic", format: "score", description: "X₁…X₅ individual components" },
  { key: "z_score_zone", label: "Z-Score Zone", category: "forensic", format: "score", description: "> 2.99 Safe · 1.81–2.99 Grey · < 1.81 Distress" },
  { key: "piotroski_f_score", label: "Piotroski F-Score", category: "forensic", format: "score", description: "Sum of 9 binary signals (0–9)" },
  { key: "piotroski_signals", label: "Piotroski Signals", category: "forensic", format: "score", description: "Individual pass/fail signals" },
  { key: "piotroski_strength", label: "Piotroski Strength", category: "forensic", format: "score", description: "≥ 7 Strong · 4–6 Moderate · ≤ 3 Weak" },
  { key: "beneish_m_score", label: "Beneish M-Score", category: "forensic", format: "score", description: "−4.84 + Σ(weighted index ratios)" },
  { key: "beneish_components", label: "Beneish Components", category: "forensic", format: "score", description: "DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA" },
  { key: "manipulation_risk", label: "Manipulation Risk", category: "forensic", format: "score", description: "> −1.78 High · ≤ −1.78 Low" },
  { key: "risk_flags", label: "Risk Flags", category: "forensic", format: "score", description: "Specific accounting risk indicators" },

  // =========================================================================
  // SHAREHOLDER (10)
  // =========================================================================
  { key: "payout_ratio", label: "Payout Ratio", category: "shareholder", format: "percent", description: "|Dividends| ÷ Net Income" },
  { key: "dividend_payout_ratio", label: "Dividend Payout Ratio", category: "shareholder", format: "percent", description: "|Dividends| ÷ Net Income" },
  { key: "retention_ratio", label: "Retention Ratio", category: "shareholder", format: "percent", description: "1 − Payout Ratio" },
  { key: "buyback_ratio", label: "Buyback Ratio", category: "shareholder", format: "percent", description: "|Share Repurchases| ÷ Net Income" },
  { key: "shareholder_yield", label: "Shareholder Yield", category: "shareholder", format: "percent", description: "(|Dividends| + |Buybacks|) ÷ Market Cap" },
  { key: "total_capital_returned", label: "Total Capital Returned", category: "shareholder", format: "currency", description: "|Dividends| + |Buybacks|" },
  { key: "net_debt_paydown", label: "Net Debt Paydown", category: "shareholder", format: "currency", description: "|Debt Repaid| − |Debt Issued|" },
  { key: "total_shareholder_return_allocation", label: "TSR Allocation", category: "shareholder", format: "percent", description: "(Capital Returned + Debt Paydown) ÷ OCF" },
  { key: "dividends_per_share", label: "Dividends / Share", category: "shareholder", format: "currency", description: "|Dividends| ÷ Shares Outstanding" },
  { key: "buyback_per_share", label: "Buyback / Share", category: "shareholder", format: "currency", description: "|Buybacks| ÷ Shares Outstanding" },

  // =========================================================================
  // PER SHARE (13)
  // =========================================================================
  { key: "revenue_per_share_ps", label: "Revenue / Share", category: "per_share", format: "currency", description: "Revenue ÷ Shares Outstanding" },
  { key: "gross_profit_per_share", label: "Gross Profit / Share", category: "per_share", format: "currency", description: "Gross Profit ÷ Shares Outstanding" },
  { key: "operating_income_per_share", label: "Operating Income / Share", category: "per_share", format: "currency", description: "Operating Income ÷ Shares Outstanding" },
  { key: "ebitda_per_share", label: "EBITDA / Share", category: "per_share", format: "currency", description: "EBITDA ÷ Shares Outstanding" },
  { key: "net_income_per_share", label: "Net Income / Share", category: "per_share", format: "currency", description: "Net Income ÷ Shares Outstanding" },
  { key: "book_value_per_share_ps", label: "Book Value / Share", category: "per_share", format: "currency", description: "Total Equity ÷ Shares Outstanding" },
  { key: "tangible_book_value_per_share_ps", label: "Tangible BV / Share", category: "per_share", format: "currency", description: "(Equity − Goodwill − Intangibles) ÷ Shares Outstanding" },
  { key: "operating_cash_flow_per_share", label: "OCF / Share", category: "per_share", format: "currency", description: "OCF ÷ Shares Outstanding" },
  { key: "free_cash_flow_per_share", label: "FCF / Share", category: "per_share", format: "currency", description: "FCF ÷ Shares Outstanding" },
  { key: "dividends_per_share_ps", label: "Dividends / Share", category: "per_share", format: "currency", description: "|Dividends| ÷ Shares Outstanding" },
  { key: "total_debt_per_share", label: "Total Debt / Share", category: "per_share", format: "currency", description: "Total Debt ÷ Shares Outstanding" },
  { key: "net_debt_per_share", label: "Net Debt / Share", category: "per_share", format: "currency", description: "Net Debt ÷ Shares Outstanding" },
  { key: "cash_per_share", label: "Cash / Share", category: "per_share", format: "currency", description: "Cash & Equivalents ÷ Shares Outstanding" },
];

// ---------------------------------------------------------------------------
// Lookup helpers
// ---------------------------------------------------------------------------

/** Map from metric key → MetricMeta for O(1) lookup */
export const METRIC_MAP: Record<string, MetricMeta> = Object.fromEntries(
  METRIC_METADATA.map((m) => [m.key, m]),
);

/** Get all metrics belonging to a given category */
export function getMetricsByCategory(category: string): MetricMeta[] {
  return METRIC_METADATA.filter((m) => m.category === category);
}

/** Get a single metric's metadata, or undefined if not found */
export function getMetricMeta(key: string): MetricMeta | undefined {
  return METRIC_MAP[key];
}
