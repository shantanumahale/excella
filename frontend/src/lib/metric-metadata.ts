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
  { key: "gross_margin", label: "Gross Margin", category: "profitability", format: "percent", description: "Revenue minus cost of goods sold, divided by revenue" },
  { key: "operating_margin", label: "Operating Margin", category: "profitability", format: "percent", description: "Operating income as a percentage of revenue" },
  { key: "net_margin", label: "Net Margin", category: "profitability", format: "percent", description: "Net income as a percentage of revenue" },
  { key: "ebitda_margin", label: "EBITDA Margin", category: "profitability", format: "percent", description: "EBITDA as a percentage of revenue" },
  { key: "ebit_margin", label: "EBIT Margin", category: "profitability", format: "percent", description: "Earnings before interest and taxes as a percentage of revenue" },
  { key: "return_on_assets", label: "Return on Assets", category: "profitability", format: "percent", description: "Net income divided by total assets" },
  { key: "return_on_equity", label: "Return on Equity", category: "profitability", format: "percent", description: "Net income divided by shareholders' equity" },
  { key: "return_on_capital_employed", label: "Return on Capital Employed", category: "profitability", format: "percent", description: "EBIT divided by capital employed (total assets minus current liabilities)" },
  { key: "return_on_invested_capital", label: "Return on Invested Capital", category: "profitability", format: "percent", description: "NOPAT divided by invested capital" },
  { key: "effective_tax_rate", label: "Effective Tax Rate", category: "profitability", format: "percent", description: "Income tax expense divided by pre-tax income" },
  { key: "nopat", label: "NOPAT", category: "profitability", format: "currency", description: "Net operating profit after tax" },
  { key: "invested_capital", label: "Invested Capital", category: "profitability", format: "currency", description: "Total debt plus equity minus excess cash" },
  { key: "capital_employed", label: "Capital Employed", category: "profitability", format: "currency", description: "Total assets minus current liabilities" },
  { key: "rd_intensity", label: "R&D Intensity", category: "profitability", format: "percent", description: "Research and development expense as a percentage of revenue" },
  { key: "sga_ratio", label: "SG&A Ratio", category: "profitability", format: "percent", description: "Selling, general and administrative expense as a percentage of revenue" },
  { key: "sbc_pct_revenue", label: "SBC % Revenue", category: "profitability", format: "percent", description: "Stock-based compensation as a percentage of revenue" },

  // =========================================================================
  // LIQUIDITY (10)
  // =========================================================================
  { key: "current_ratio", label: "Current Ratio", category: "liquidity", format: "ratio", description: "Current assets divided by current liabilities" },
  { key: "quick_ratio", label: "Quick Ratio", category: "liquidity", format: "ratio", description: "Liquid assets (ex-inventory) divided by current liabilities" },
  { key: "cash_ratio", label: "Cash Ratio", category: "liquidity", format: "ratio", description: "Cash and equivalents divided by current liabilities" },
  { key: "net_working_capital", label: "Net Working Capital", category: "liquidity", format: "currency", description: "Current assets minus current liabilities" },
  { key: "nwc_pct_revenue", label: "NWC % Revenue", category: "liquidity", format: "percent", description: "Net working capital as a percentage of revenue" },
  { key: "days_inventory_outstanding", label: "Days Inventory Outstanding", category: "liquidity", format: "number", description: "Average number of days inventory is held before sale" },
  { key: "days_sales_outstanding", label: "Days Sales Outstanding", category: "liquidity", format: "number", description: "Average number of days to collect receivables" },
  { key: "days_payable_outstanding", label: "Days Payable Outstanding", category: "liquidity", format: "number", description: "Average number of days to pay suppliers" },
  { key: "cash_conversion_cycle", label: "Cash Conversion Cycle", category: "liquidity", format: "number", description: "DIO + DSO - DPO; days to convert investment into cash flows" },
  { key: "defensive_interval", label: "Defensive Interval", category: "liquidity", format: "number", description: "Number of days a company can operate from liquid assets without revenue" },

  // =========================================================================
  // LEVERAGE (10)
  // =========================================================================
  { key: "total_debt", label: "Total Debt", category: "leverage", format: "currency", description: "Sum of short-term and long-term debt" },
  { key: "net_debt", label: "Net Debt", category: "leverage", format: "currency", description: "Total debt minus cash and equivalents" },
  { key: "debt_to_equity", label: "Debt-to-Equity", category: "leverage", format: "ratio", description: "Total debt divided by shareholders' equity" },
  { key: "debt_to_assets", label: "Debt-to-Assets", category: "leverage", format: "ratio", description: "Total debt divided by total assets" },
  { key: "debt_to_ebitda", label: "Debt-to-EBITDA", category: "leverage", format: "ratio", description: "Total debt divided by EBITDA" },
  { key: "interest_coverage", label: "Interest Coverage", category: "leverage", format: "ratio", description: "EBIT divided by interest expense" },
  { key: "equity_multiplier", label: "Equity Multiplier", category: "leverage", format: "ratio", description: "Total assets divided by shareholders' equity" },
  { key: "debt_to_capital", label: "Debt-to-Capital", category: "leverage", format: "ratio", description: "Total debt divided by total capital (debt + equity)" },
  { key: "long_term_debt_to_equity", label: "LT Debt-to-Equity", category: "leverage", format: "ratio", description: "Long-term debt divided by shareholders' equity" },
  { key: "financial_leverage_ratio", label: "Financial Leverage Ratio", category: "leverage", format: "ratio", description: "Average total assets divided by average equity" },

  // =========================================================================
  // EFFICIENCY (10)
  // =========================================================================
  { key: "asset_turnover", label: "Asset Turnover", category: "efficiency", format: "ratio", description: "Revenue divided by average total assets" },
  { key: "fixed_asset_turnover", label: "Fixed Asset Turnover", category: "efficiency", format: "ratio", description: "Revenue divided by net property, plant and equipment" },
  { key: "inventory_turnover", label: "Inventory Turnover", category: "efficiency", format: "ratio", description: "COGS divided by average inventory" },
  { key: "receivables_turnover", label: "Receivables Turnover", category: "efficiency", format: "ratio", description: "Revenue divided by average accounts receivable" },
  { key: "payables_turnover", label: "Payables Turnover", category: "efficiency", format: "ratio", description: "COGS divided by average accounts payable" },
  { key: "equity_turnover", label: "Equity Turnover", category: "efficiency", format: "ratio", description: "Revenue divided by average shareholders' equity" },
  { key: "capital_expenditure_to_revenue", label: "CapEx-to-Revenue", category: "efficiency", format: "percent", description: "Capital expenditures as a percentage of revenue" },
  { key: "capex_to_depreciation", label: "CapEx-to-Depreciation", category: "efficiency", format: "ratio", description: "Capital expenditures divided by depreciation expense" },
  { key: "operating_cycle", label: "Operating Cycle", category: "efficiency", format: "number", description: "DIO + DSO; days from inventory purchase to cash collection" },
  { key: "cash_cycle", label: "Cash Cycle", category: "efficiency", format: "number", description: "Operating cycle minus days payable outstanding" },

  // =========================================================================
  // CASH FLOW (11)
  // =========================================================================
  { key: "free_cash_flow_to_firm", label: "FCFF", category: "cashflow", format: "currency", description: "Free cash flow available to all capital providers" },
  { key: "free_cash_flow_to_firm_simplified", label: "FCFF (Simplified)", category: "cashflow", format: "currency", description: "Operating cash flow minus capital expenditures" },
  { key: "free_cash_flow_to_equity", label: "FCFE", category: "cashflow", format: "currency", description: "Free cash flow available to equity holders after debt payments" },
  { key: "net_borrowing", label: "Net Borrowing", category: "cashflow", format: "currency", description: "New debt issued minus debt repaid" },
  { key: "operating_cash_flow_margin", label: "OCF Margin", category: "cashflow", format: "percent", description: "Operating cash flow as a percentage of revenue" },
  { key: "cash_flow_to_net_income", label: "Cash Flow / Net Income", category: "cashflow", format: "ratio", description: "Operating cash flow divided by net income" },
  { key: "capex_to_operating_cash_flow", label: "CapEx / OCF", category: "cashflow", format: "percent", description: "Capital expenditures as a percentage of operating cash flow" },
  { key: "cash_return_on_invested_capital", label: "Cash ROIC", category: "cashflow", format: "percent", description: "Free cash flow divided by invested capital" },
  { key: "reinvestment_rate", label: "Reinvestment Rate", category: "cashflow", format: "percent", description: "Net capital expenditure plus change in working capital, divided by NOPAT" },
  { key: "capex_to_depreciation_cf", label: "CapEx / Depreciation", category: "cashflow", format: "ratio", description: "Capital expenditures divided by depreciation (cash flow view)" },
  { key: "nopat_cf", label: "NOPAT", category: "cashflow", format: "currency", description: "Net operating profit after tax (cash flow context)" },

  // =========================================================================
  // GROWTH (15)
  // =========================================================================
  { key: "revenue_growth", label: "Revenue Growth", category: "growth", format: "percent", description: "Year-over-year change in revenue" },
  { key: "gross_profit_growth", label: "Gross Profit Growth", category: "growth", format: "percent", description: "Year-over-year change in gross profit" },
  { key: "operating_income_growth", label: "Operating Income Growth", category: "growth", format: "percent", description: "Year-over-year change in operating income" },
  { key: "ebitda_growth", label: "EBITDA Growth", category: "growth", format: "percent", description: "Year-over-year change in EBITDA" },
  { key: "net_income_growth", label: "Net Income Growth", category: "growth", format: "percent", description: "Year-over-year change in net income" },
  { key: "eps_growth", label: "EPS Growth", category: "growth", format: "percent", description: "Year-over-year change in earnings per share" },
  { key: "operating_cash_flow_growth", label: "OCF Growth", category: "growth", format: "percent", description: "Year-over-year change in operating cash flow" },
  { key: "free_cash_flow_growth", label: "FCF Growth", category: "growth", format: "percent", description: "Year-over-year change in free cash flow" },
  { key: "total_assets_growth", label: "Total Assets Growth", category: "growth", format: "percent", description: "Year-over-year change in total assets" },
  { key: "equity_growth", label: "Equity Growth", category: "growth", format: "percent", description: "Year-over-year change in shareholders' equity" },
  { key: "dividend_growth", label: "Dividend Growth", category: "growth", format: "percent", description: "Year-over-year change in dividends per share" },
  { key: "sustainable_growth_rate", label: "Sustainable Growth Rate", category: "growth", format: "percent", description: "ROE multiplied by retention ratio" },
  { key: "is_acquisition_period", label: "Acquisition Period", category: "growth", format: "boolean", description: "Whether the period includes a significant acquisition" },
  { key: "acquisition_to_revenue", label: "Acquisition / Revenue", category: "growth", format: "percent", description: "Acquisition spending as a percentage of revenue" },
  { key: "reinvestment_rate_growth", label: "Reinvestment Rate", category: "growth", format: "percent", description: "Reinvestment rate used in growth context" },

  // =========================================================================
  // DUPONT (9)
  // =========================================================================
  { key: "net_margin_dupont", label: "Net Margin", category: "dupont", format: "percent", description: "Net income divided by revenue (DuPont component)" },
  { key: "asset_turnover_dupont", label: "Asset Turnover", category: "dupont", format: "ratio", description: "Revenue divided by total assets (DuPont component)" },
  { key: "equity_multiplier_dupont", label: "Equity Multiplier", category: "dupont", format: "ratio", description: "Total assets divided by equity (DuPont component)" },
  { key: "roe_3factor", label: "ROE (3-Factor)", category: "dupont", format: "percent", description: "Net margin x asset turnover x equity multiplier" },
  { key: "tax_burden", label: "Tax Burden", category: "dupont", format: "ratio", description: "Net income divided by pre-tax income" },
  { key: "interest_burden", label: "Interest Burden", category: "dupont", format: "ratio", description: "Pre-tax income divided by EBIT" },
  { key: "operating_profit_margin", label: "Operating Profit Margin", category: "dupont", format: "percent", description: "EBIT divided by revenue (DuPont 5-factor component)" },
  { key: "roe_5factor", label: "ROE (5-Factor)", category: "dupont", format: "percent", description: "Tax burden x interest burden x OPM x asset turnover x equity multiplier" },
  { key: "tax_efficiency", label: "Tax Efficiency", category: "dupont", format: "percent", description: "One minus effective tax rate" },
  { key: "interest_efficiency", label: "Interest Efficiency", category: "dupont", format: "percent", description: "Proportion of EBIT retained after interest expense" },

  // =========================================================================
  // VALUATION (18)
  // =========================================================================
  { key: "market_cap", label: "Market Cap", category: "valuation", format: "currency", description: "Share price multiplied by shares outstanding" },
  { key: "enterprise_value", label: "Enterprise Value", category: "valuation", format: "currency", description: "Market cap plus net debt minus cash" },
  { key: "pe_ratio", label: "P/E Ratio", category: "valuation", format: "ratio", description: "Share price divided by earnings per share" },
  { key: "price_to_book", label: "Price-to-Book", category: "valuation", format: "ratio", description: "Share price divided by book value per share" },
  { key: "price_to_sales", label: "Price-to-Sales", category: "valuation", format: "ratio", description: "Market cap divided by annual revenue" },
  { key: "price_to_cash_flow", label: "Price-to-Cash Flow", category: "valuation", format: "ratio", description: "Market cap divided by operating cash flow" },
  { key: "ev_to_ebitda", label: "EV/EBITDA", category: "valuation", format: "ratio", description: "Enterprise value divided by EBITDA" },
  { key: "ev_to_ebit", label: "EV/EBIT", category: "valuation", format: "ratio", description: "Enterprise value divided by EBIT" },
  { key: "ev_to_revenue", label: "EV/Revenue", category: "valuation", format: "ratio", description: "Enterprise value divided by revenue" },
  { key: "ev_to_fcf", label: "EV/FCF", category: "valuation", format: "ratio", description: "Enterprise value divided by free cash flow" },
  { key: "earnings_yield", label: "Earnings Yield", category: "valuation", format: "percent", description: "Earnings per share divided by share price" },
  { key: "fcf_yield", label: "FCF Yield", category: "valuation", format: "percent", description: "Free cash flow per share divided by share price" },
  { key: "dividend_yield", label: "Dividend Yield", category: "valuation", format: "percent", description: "Annual dividends per share divided by share price" },
  { key: "peg_ratio", label: "PEG Ratio", category: "valuation", format: "ratio", description: "P/E ratio divided by earnings growth rate" },
  { key: "book_value_per_share", label: "Book Value / Share", category: "valuation", format: "currency", description: "Total equity divided by shares outstanding" },
  { key: "tangible_book_value_per_share", label: "Tangible BV / Share", category: "valuation", format: "currency", description: "Tangible equity divided by shares outstanding" },
  { key: "revenue_per_share", label: "Revenue / Share", category: "valuation", format: "currency", description: "Total revenue divided by shares outstanding" },
  { key: "graham_number", label: "Graham Number", category: "valuation", format: "currency", description: "Square root of (22.5 x EPS x BVPS); intrinsic value estimate" },

  // =========================================================================
  // QUALITY (10)
  // =========================================================================
  { key: "accruals_ratio", label: "Accruals Ratio", category: "quality", format: "ratio", description: "Non-cash portion of earnings relative to total assets" },
  { key: "sloan_ratio", label: "Sloan Ratio", category: "quality", format: "ratio", description: "Accrual component of earnings; lower is higher quality" },
  { key: "cash_flow_to_earnings", label: "Cash Flow / Earnings", category: "quality", format: "ratio", description: "Operating cash flow divided by net income" },
  { key: "earnings_quality_score", label: "Earnings Quality Score", category: "quality", format: "score", description: "Composite score assessing sustainability of earnings" },
  { key: "revenue_vs_receivables_divergence", label: "Revenue vs Receivables Divergence", category: "quality", format: "percent", description: "Difference between revenue growth and receivables growth" },
  { key: "net_income_vs_ocf_divergence", label: "Net Income vs OCF Divergence", category: "quality", format: "percent", description: "Difference between net income growth and OCF growth" },
  { key: "capex_consistency", label: "CapEx Consistency", category: "quality", format: "ratio", description: "Consistency of capital expenditures over time" },
  { key: "organic_revenue_flag", label: "Organic Revenue Flag", category: "quality", format: "boolean", description: "Whether revenue growth appears organic (not acquisition-driven)" },
  { key: "sga_efficiency", label: "SG&A Efficiency", category: "quality", format: "ratio", description: "Change in SG&A relative to change in revenue" },
  { key: "depreciation_to_capex", label: "Depreciation / CapEx", category: "quality", format: "ratio", description: "Depreciation divided by capital expenditures" },

  // =========================================================================
  // FORENSIC (10)
  // =========================================================================
  { key: "altman_z_score", label: "Altman Z-Score", category: "forensic", format: "score", description: "Bankruptcy prediction score; above 2.99 is safe" },
  { key: "altman_z_components", label: "Altman Z Components", category: "forensic", format: "score", description: "Individual components of the Altman Z-Score" },
  { key: "z_score_zone", label: "Z-Score Zone", category: "forensic", format: "score", description: "Classification: safe, grey, or distress zone" },
  { key: "piotroski_f_score", label: "Piotroski F-Score", category: "forensic", format: "score", description: "Fundamental strength score from 0 to 9" },
  { key: "piotroski_signals", label: "Piotroski Signals", category: "forensic", format: "score", description: "Individual pass/fail signals of the Piotroski test" },
  { key: "piotroski_strength", label: "Piotroski Strength", category: "forensic", format: "score", description: "Qualitative assessment of Piotroski score (strong, moderate, weak)" },
  { key: "beneish_m_score", label: "Beneish M-Score", category: "forensic", format: "score", description: "Earnings manipulation detection score; above -1.78 suggests manipulation" },
  { key: "beneish_components", label: "Beneish Components", category: "forensic", format: "score", description: "Individual components of the Beneish M-Score" },
  { key: "manipulation_risk", label: "Manipulation Risk", category: "forensic", format: "score", description: "Likelihood of earnings manipulation (low, moderate, high)" },
  { key: "risk_flags", label: "Risk Flags", category: "forensic", format: "score", description: "Specific accounting risk indicators detected" },

  // =========================================================================
  // SHAREHOLDER (10)
  // =========================================================================
  { key: "payout_ratio", label: "Payout Ratio", category: "shareholder", format: "percent", description: "Total dividends plus buybacks divided by net income" },
  { key: "dividend_payout_ratio", label: "Dividend Payout Ratio", category: "shareholder", format: "percent", description: "Dividends paid divided by net income" },
  { key: "retention_ratio", label: "Retention Ratio", category: "shareholder", format: "percent", description: "Proportion of net income retained (1 - payout ratio)" },
  { key: "buyback_ratio", label: "Buyback Ratio", category: "shareholder", format: "percent", description: "Share repurchases as a percentage of market cap" },
  { key: "shareholder_yield", label: "Shareholder Yield", category: "shareholder", format: "percent", description: "Dividend yield plus buyback yield plus debt paydown yield" },
  { key: "total_capital_returned", label: "Total Capital Returned", category: "shareholder", format: "currency", description: "Dividends plus share repurchases" },
  { key: "net_debt_paydown", label: "Net Debt Paydown", category: "shareholder", format: "currency", description: "Net reduction in debt over the period" },
  { key: "total_shareholder_return_allocation", label: "TSR Allocation", category: "shareholder", format: "percent", description: "Allocation of total capital returns between dividends and buybacks" },
  { key: "dividends_per_share", label: "Dividends / Share", category: "shareholder", format: "currency", description: "Total dividends paid divided by shares outstanding" },
  { key: "buyback_per_share", label: "Buyback / Share", category: "shareholder", format: "currency", description: "Total share repurchases divided by shares outstanding" },

  // =========================================================================
  // PER SHARE (13)
  // =========================================================================
  { key: "revenue_per_share_ps", label: "Revenue / Share", category: "per_share", format: "currency", description: "Total revenue divided by shares outstanding" },
  { key: "gross_profit_per_share", label: "Gross Profit / Share", category: "per_share", format: "currency", description: "Gross profit divided by shares outstanding" },
  { key: "operating_income_per_share", label: "Operating Income / Share", category: "per_share", format: "currency", description: "Operating income divided by shares outstanding" },
  { key: "ebitda_per_share", label: "EBITDA / Share", category: "per_share", format: "currency", description: "EBITDA divided by shares outstanding" },
  { key: "net_income_per_share", label: "Net Income / Share", category: "per_share", format: "currency", description: "Net income divided by shares outstanding (EPS)" },
  { key: "book_value_per_share_ps", label: "Book Value / Share", category: "per_share", format: "currency", description: "Book value of equity divided by shares outstanding" },
  { key: "tangible_book_value_per_share_ps", label: "Tangible BV / Share", category: "per_share", format: "currency", description: "Tangible book value divided by shares outstanding" },
  { key: "operating_cash_flow_per_share", label: "OCF / Share", category: "per_share", format: "currency", description: "Operating cash flow divided by shares outstanding" },
  { key: "free_cash_flow_per_share", label: "FCF / Share", category: "per_share", format: "currency", description: "Free cash flow divided by shares outstanding" },
  { key: "dividends_per_share_ps", label: "Dividends / Share", category: "per_share", format: "currency", description: "Total dividends divided by shares outstanding" },
  { key: "total_debt_per_share", label: "Total Debt / Share", category: "per_share", format: "currency", description: "Total debt divided by shares outstanding" },
  { key: "net_debt_per_share", label: "Net Debt / Share", category: "per_share", format: "currency", description: "Net debt divided by shares outstanding" },
  { key: "cash_per_share", label: "Cash / Share", category: "per_share", format: "currency", description: "Cash and equivalents divided by shares outstanding" },
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
