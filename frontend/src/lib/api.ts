import axios from "axios";
import type {
  Company,
  CompanyListItem,
  DCFParams,
  DerivedMetrics,
  FinancialStatement,
  FredObservation,
  FredSeries,
  MetricCatalogue,
  PaginatedResponse,
  PriceBar,
  PriceReturns,
  ScreenerRequest,
  ScreenerResult,
  SensitivityResult,
  ValuationHistoryPoint,
  ValuationResult,
} from "./types";

// ---------------------------------------------------------------------------
// Axios instance – proxied through Next.js rewrites so we never hit CORS
// ---------------------------------------------------------------------------

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// ---------------------------------------------------------------------------
// Companies
// ---------------------------------------------------------------------------

export interface GetCompaniesParams {
  sector?: string;
  industry?: string;
  exchange?: string;
  search?: string;
  offset?: number;
  limit?: number;
}

export async function getCompanies(
  params?: GetCompaniesParams,
): Promise<PaginatedResponse<CompanyListItem>> {
  const { data } = await api.get<PaginatedResponse<CompanyListItem>>(
    "/companies",
    { params },
  );
  return data;
}

export async function getCompany(ticker: string): Promise<Company> {
  const { data } = await api.get<Company>(`/companies/${ticker}`);
  return data;
}

// ---------------------------------------------------------------------------
// Financials
// ---------------------------------------------------------------------------

export interface GetFinancialsParams {
  statement_type?: string;
  period_type?: string;
  limit?: number;
}

export async function getFinancials(
  ticker: string,
  params?: GetFinancialsParams,
): Promise<FinancialStatement[]> {
  const { data } = await api.get<FinancialStatement[]>(
    `/companies/${ticker}/financials`,
    { params },
  );
  return data;
}

export interface GetMetricsParams {
  period_type?: string;
  limit?: number;
}

export async function getMetrics(
  ticker: string,
  params?: GetMetricsParams,
): Promise<DerivedMetrics[]> {
  const { data } = await api.get<DerivedMetrics[]>(
    `/companies/${ticker}/metrics`,
    { params },
  );
  return data;
}

export async function getLatestMetrics(
  ticker: string,
): Promise<DerivedMetrics> {
  const { data } = await api.get<DerivedMetrics>(
    `/companies/${ticker}/metrics/latest`,
  );
  return data;
}

// ---------------------------------------------------------------------------
// Prices
// ---------------------------------------------------------------------------

export interface GetPricesParams {
  start?: string;
  end?: string;
  offset?: number;
  limit?: number;
}

export async function getPrices(
  ticker: string,
  params?: GetPricesParams,
): Promise<PaginatedResponse<PriceBar>> {
  const { data } = await api.get<PaginatedResponse<PriceBar>>(
    `/prices/${ticker}`,
    { params },
  );
  return data;
}

export async function getLatestPrice(ticker: string): Promise<PriceBar> {
  const { data } = await api.get<PriceBar>(
    `/prices/${ticker}/latest`,
  );
  return data;
}

export async function getReturns(ticker: string): Promise<PriceReturns> {
  const { data } = await api.get<PriceReturns>(
    `/prices/${ticker}/returns`,
  );
  return data;
}

// ---------------------------------------------------------------------------
// Macro
// ---------------------------------------------------------------------------

export async function getMacroSeries(): Promise<FredSeries[]> {
  const { data } = await api.get<FredSeries[]>("/macro/series");
  return data;
}

export interface GetMacroObservationsParams {
  start?: string;
  end?: string;
  offset?: number;
  limit?: number;
}

export async function getMacroObservations(
  seriesId: string,
  params?: GetMacroObservationsParams,
): Promise<PaginatedResponse<FredObservation>> {
  const { data } = await api.get<PaginatedResponse<FredObservation>>(
    `/macro/series/${seriesId}`,
    { params },
  );
  return data;
}

export async function getMacroLatest(
  seriesId: string,
): Promise<FredObservation> {
  const { data } = await api.get<FredObservation>(
    `/macro/series/${seriesId}/latest`,
  );
  return data;
}

export async function getMacroAllLatest(): Promise<Record<string, FredObservation>> {
  const { data } = await api.get<Record<string, FredObservation>>(
    "/macro/series/latest",
  );
  return data;
}

// ---------------------------------------------------------------------------
// Screener
// ---------------------------------------------------------------------------

export async function runScreener(
  body: ScreenerRequest,
): Promise<PaginatedResponse<ScreenerResult>> {
  const { data } = await api.post<PaginatedResponse<ScreenerResult>>(
    "/screener",
    body,
  );
  return data;
}

export async function getMetricCatalogue(): Promise<MetricCatalogue> {
  const { data } = await api.get<MetricCatalogue>("/screener/metrics");
  return data;
}

// ---------------------------------------------------------------------------
// Valuation
// ---------------------------------------------------------------------------

export async function getValuation(ticker: string): Promise<{ ticker: string; period_end: string; valuation_models: ValuationResult }> {
  const { data } = await api.get(`/companies/${ticker}/valuation`);
  return data;
}

export async function runCustomDCF(
  ticker: string,
  params: DCFParams,
): Promise<ValuationResult> {
  const { data } = await api.post<ValuationResult>(
    `/companies/${ticker}/valuation/dcf`,
    params,
  );
  return data;
}

export async function getValuationSensitivity(
  ticker: string,
): Promise<SensitivityResult> {
  const { data } = await api.get<SensitivityResult>(
    `/companies/${ticker}/valuation/sensitivity`,
  );
  return data;
}

export async function getValuationComps(ticker: string): Promise<{ ticker: string } & import("./types").CompsResult> {
  const { data } = await api.get(`/companies/${ticker}/valuation/comps`);
  return data;
}

export async function getValuationHistory(
  ticker: string,
  limit?: number,
): Promise<{ ticker: string; history: ValuationHistoryPoint[] }> {
  const { data } = await api.get(`/companies/${ticker}/valuation/history`, {
    params: limit ? { limit } : undefined,
  });
  return data;
}

// ---------------------------------------------------------------------------
// System
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: string;
  version?: string;
  uptime?: number;
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

// ---------------------------------------------------------------------------
// Export the raw axios instance for advanced use
// ---------------------------------------------------------------------------

export default api;
