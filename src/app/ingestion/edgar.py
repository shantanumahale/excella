"""SEC EDGAR ingestor – company filings and XBRL financial facts."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import requests

from app.config import settings
from app.db.models import Company, Filing, FinancialStatement
from app.ingestion.base import BaseIngestor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# XBRL tag -> canonical field mapping
# Keys = canonical names, values = list of XBRL us-gaap tags to try (first match wins)
# ---------------------------------------------------------------------------

INCOME_TAGS: dict[str, list[str]] = {
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
        "SalesRevenueServicesNet",
        "TotalRevenuesAndOtherIncome",
        "RevenueNet",
        "SalesRevenueServicesGross",
    ],
    "cost_of_revenue": [
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
        "CostOfGoodsSold",
        "CostOfServices",
        "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization",
    ],
    "gross_profit": ["GrossProfit"],
    "research_and_development": [
        "ResearchAndDevelopmentExpense",
        "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
        "ResearchAndDevelopmentExpenseSoftwareExcludingAcquiredInProcessCost",
    ],
    "selling_general_admin": [
        "SellingGeneralAndAdministrativeExpense",
        "GeneralAndAdministrativeExpense",
        "SellingAndMarketingExpense",
        "MarketingAndSellingExpense",
    ],
    "operating_expenses": [
        "OperatingExpenses",
        "CostsAndExpenses",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
        "IncomeLossFromContinuingOperations",
    ],
    "interest_expense": [
        "InterestExpense",
        "InterestExpenseDebt",
        "InterestIncomeExpenseNet",
        "InterestExpenseNetOfInterestCapitalized",
    ],
    "interest_income": [
        "InterestIncome",
        "InvestmentIncomeInterest",
        "InterestIncomeOther",
        "InvestmentIncomeInterestAndDividend",
    ],
    "other_income_expense": [
        "OtherNonoperatingIncomeExpense",
        "NonoperatingIncomeExpense",
        "OtherIncomeExpenseNet",
        "OtherIncome",
    ],
    "pretax_income": [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic",
    ],
    "income_tax": [
        "IncomeTaxExpenseBenefit",
        "IncomeTaxesPaidNet",
        "CurrentIncomeTaxExpenseBenefit",
    ],
    "net_income": [
        "NetIncomeLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
        "ProfitLoss",
        "NetIncomeLossAttributableToParent",
    ],
    "eps_basic": ["EarningsPerShareBasic"],
    "eps_diluted": ["EarningsPerShareDiluted"],
    "shares_basic": [
        "WeightedAverageNumberOfSharesOutstandingBasic",
        "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
        "CommonStockSharesOutstanding",
    ],
    "shares_diluted": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
    ],
    "ebitda": [
        "EarningsBeforeInterestTaxesDepreciationAndAmortization",
    ],
    "depreciation_amortization": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
        "Depreciation",
    ],
    "stock_based_compensation": [
        "ShareBasedCompensation",
        "AllocatedShareBasedCompensationExpense",
        "StockBasedCompensation",
        "SharebasedCompensation",
    ],
}

BALANCE_TAGS: dict[str, list[str]] = {
    "cash_and_equivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        "Cash",
    ],
    "short_term_investments": [
        "ShortTermInvestments",
        "MarketableSecuritiesCurrent",
        "AvailableForSaleSecuritiesCurrent",
        "OtherShortTermInvestments",
    ],
    "accounts_receivable": [
        "AccountsReceivableNetCurrent",
        "AccountsReceivableNet",
        "ReceivablesNetCurrent",
        "TradeAndOtherReceivablesNetCurrent",
        "ContractWithCustomerReceivableAfterAllowanceForCreditLossCurrent",
    ],
    "inventory": [
        "InventoryNet",
        "InventoryFinishedGoods",
        "InventoryFinishedGoodsAndWorkInProcess",
    ],
    "other_current_assets": [
        "OtherAssetsCurrent",
        "PrepaidExpenseAndOtherAssetsCurrent",
    ],
    "total_current_assets": ["AssetsCurrent"],
    "property_plant_equipment": [
        "PropertyPlantAndEquipmentNet",
        "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization",
        "PropertyPlantAndEquipmentGross",
    ],
    "goodwill": ["Goodwill"],
    "intangible_assets": [
        "IntangibleAssetsNetExcludingGoodwill",
        "FiniteLivedIntangibleAssetsNet",
        "IndefiniteLivedIntangibleAssetsExcludingGoodwill",
    ],
    "total_assets": ["Assets"],
    "accounts_payable": [
        "AccountsPayableCurrent",
        "AccountsPayableAndAccruedLiabilitiesCurrent",
        "AccountsPayableTradeCurrent",
    ],
    "short_term_debt": [
        "ShortTermBorrowings",
        "DebtCurrent",
        "LongTermDebtCurrent",
        "CommercialPaper",
        "ShortTermDebtAndCapitalLeaseObligationsCurrent",
    ],
    "current_portion_long_term_debt": [
        "LongTermDebtCurrent",
        "CurrentPortionOfLongTermDebt",
    ],
    "other_current_liabilities": [
        "OtherLiabilitiesCurrent",
        "AccruedLiabilitiesCurrent",
        "OtherAccruedLiabilitiesCurrent",
    ],
    "total_current_liabilities": ["LiabilitiesCurrent"],
    "long_term_debt": [
        "LongTermDebtNoncurrent",
        "LongTermDebt",
        "LongTermDebtAndCapitalLeaseObligations",
        "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
    ],
    "total_liabilities": [
        "Liabilities",
        "LiabilitiesAndStockholdersEquity",  # fallback: will need equity subtraction
    ],
    "common_stock": [
        "CommonStockValue",
        "CommonStocksIncludingAdditionalPaidInCapital",
    ],
    "total_stockholders_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "retained_earnings": [
        "RetainedEarningsAccumulatedDeficit",
    ],
    "minority_interest": [
        "MinorityInterest",
        "RedeemableNoncontrollingInterestEquityCarryingAmount",
        "MinorityInterestInNetIncomeLossOfConsolidatedEntities",
    ],
    "total_equity": [
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "StockholdersEquity",
    ],
}

CASHFLOW_TAGS: dict[str, list[str]] = {
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "depreciation_amortization_cf": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
        "Depreciation",
    ],
    "capital_expenditure": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "CapitalExpenditure",
        "PaymentsToAcquireProductiveAssets",
        "PaymentsForCapitalImprovements",
    ],
    "investing_cash_flow": [
        "NetCashProvidedByUsedInInvestingActivities",
        "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations",
    ],
    "acquisitions": [
        "PaymentsToAcquireBusinessesNetOfCashAcquired",
        "PaymentsToAcquireBusinessesGross",
        "PaymentsToAcquireBusinessesAndInterestInAffiliates",
    ],
    "dividends_paid": [
        "PaymentsOfDividendsCommonStock",
        "PaymentsOfDividends",
        "PaymentsOfOrdinaryDividends",
        "Dividends",
        "DividendsPaid",
    ],
    "share_repurchase": [
        "PaymentsForRepurchaseOfCommonStock",
        "PaymentsForRepurchaseOfEquity",
        "StockRepurchasedAndRetiredDuringPeriodValue",
    ],
    "debt_issuance": [
        "ProceedsFromIssuanceOfLongTermDebt",
        "ProceedsFromIssuanceOfDebt",
        "ProceedsFromDebtNetOfIssuanceCosts",
    ],
    "debt_repayment": [
        "RepaymentsOfLongTermDebt",
        "RepaymentsOfDebt",
        "RepaymentsOfLongTermDebtAndCapitalSecurities",
    ],
    "financing_cash_flow": [
        "NetCashProvidedByUsedInFinancingActivities",
        "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations",
    ],
    "net_change_in_cash": [
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
        "CashAndCashEquivalentsPeriodIncreaseDecrease",
        "CashPeriodIncreaseDecrease",
    ],
}

STATEMENT_TAG_MAP: dict[str, dict[str, list[str]]] = {
    "income": INCOME_TAGS,
    "balance": BALANCE_TAGS,
    "cashflow": CASHFLOW_TAGS,
}


class EdgarIngestor(BaseIngestor):
    """Ingest company data from SEC EDGAR (submissions + XBRL company facts)."""

    source_name = "edgar"

    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
    COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

    def __init__(self) -> None:
        super().__init__()
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": settings.edgar_user_agent,
                "Accept-Encoding": "gzip, deflate",
            }
        )

    # -- HTTP with rate limiting --

    def _get(self, url: str) -> requests.Response:
        """GET with 10-req/s rate-limit compliance."""
        time.sleep(0.1)
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        return resp

    # -- Helpers --

    @staticmethod
    def _pad_cik(cik: str) -> str:
        """Zero-pad CIK to 10 digits."""
        return cik.zfill(10)

    # -- Core ingestion --

    def _upsert_company(self, submissions: dict[str, Any]) -> Company:
        """Upsert a Company record from EDGAR submissions data."""
        cik = str(submissions.get("cik", ""))
        name = submissions.get("name", "")
        tickers = submissions.get("tickers", [])
        ticker = tickers[0] if tickers else None
        sic = submissions.get("sic", "")
        sic_description = submissions.get("sicDescription", "")
        ein = submissions.get("ein", "")
        state = submissions.get("stateOfIncorporation", "")
        fiscal_year_end = submissions.get("fiscalYearEnd", "")

        company = self.db.query(Company).filter(Company.cik == cik).first()
        if company is None:
            company = Company(cik=cik)
            self.db.add(company)

        company.name = name
        company.ticker = ticker
        company.sic_code = sic
        company.sic_description = sic_description
        company.ein = ein
        company.state_of_incorporation = state
        company.fiscal_year_end = fiscal_year_end

        self.db.commit()
        self.db.refresh(company)
        logger.info("Upserted company: cik=%s name=%s", cik, name)
        return company

    def _upsert_filings(
        self, company: Company, submissions: dict[str, Any]
    ) -> int:
        """Upsert Filing records from recent filings in the submissions payload."""
        recent = submissions.get("filings", {}).get("recent", {})
        if not recent:
            logger.warning("No recent filings found for cik=%s", company.cik)
            return 0

        accession_numbers = recent.get("accessionNumber", [])
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        primary_docs = recent.get("primaryDocument", [])
        descriptions = recent.get("primaryDocDescription", [])

        count = 0
        for i, accession in enumerate(accession_numbers):
            filing = (
                self.db.query(Filing)
                .filter(
                    Filing.company_id == company.id,
                    Filing.accession_number == accession,
                )
                .first()
            )
            if filing is None:
                filing = Filing(
                    company_id=company.id,
                    accession_number=accession,
                )
                self.db.add(filing)

            filing.form_type = forms[i] if i < len(forms) else None
            filing.filing_date = (
                datetime.strptime(filing_dates[i], "%Y-%m-%d").date()
                if i < len(filing_dates)
                else None
            )
            filing.primary_document = (
                primary_docs[i] if i < len(primary_docs) else None
            )
            filing.description = (
                descriptions[i] if i < len(descriptions) else None
            )
            count += 1

        self.db.commit()
        logger.info(
            "Upserted %d filings for cik=%s", count, company.cik
        )
        return count

    def _parse_xbrl_facts(
        self,
        company: Company,
        facts_json: dict[str, Any],
    ) -> int:
        """Parse XBRL company facts into FinancialStatement records.

        Groups observations by (period_end, fiscal_period) and creates three
        statement rows per group: income_statement, balance_sheet, cash_flow_statement.
        """
        us_gaap = facts_json.get("facts", {}).get("us-gaap", {})
        if not us_gaap:
            logger.warning("No us-gaap facts for cik=%s", company.cik)
            return 0

        # Build a lookup: xbrl_tag -> list of observation dicts
        tag_observations: dict[str, list[dict]] = {}
        for tag_name, tag_data in us_gaap.items():
            units = tag_data.get("units", {})
            for unit_key, obs_list in units.items():
                tag_observations[tag_name] = obs_list

        # For each statement type, resolve canonical values grouped by period key
        # period_key = (period_end_date, fiscal_year, fiscal_period)
        # Structure: {stmt_type: {period_key: {canonical_field: value}}}
        grouped: dict[str, dict[tuple, dict[str, Any]]] = {
            st: defaultdict(dict) for st in STATEMENT_TAG_MAP
        }

        for stmt_type, tag_map in STATEMENT_TAG_MAP.items():
            for canonical_name, xbrl_tags in tag_map.items():
                for xbrl_tag in xbrl_tags:
                    observations = tag_observations.get(xbrl_tag)
                    if not observations:
                        continue
                    for obs in observations:
                        period_end = obs.get("end")
                        fy = obs.get("fy")
                        fp = obs.get("fp")
                        val = obs.get("val")
                        if period_end is None or val is None:
                            continue
                        key = (period_end, fy, fp)
                        # First tag match wins — don't overwrite
                        if canonical_name not in grouped[stmt_type][key]:
                            grouped[stmt_type][key][canonical_name] = val
                    # NOTE: Do NOT break here. Companies change XBRL tags
                    # across filing periods (e.g. AAPL switched from "Revenues"
                    # to "RevenueFromContractWithCustomerExcludingAssessedTax").
                    # We must process all alternative tags so every period gets
                    # data.  Per-period dedup is handled by the "first tag match
                    # wins" check above.

        # Post-process: compute derived fields from available data
        all_keys = set()
        for stmt_data in grouped.values():
            all_keys.update(stmt_data.keys())

        for period_key in all_keys:
            inc = grouped["income"].get(period_key, {})
            cf = grouped["cashflow"].get(period_key, {})

            if not inc:
                continue

            # Pull D&A from cashflow into income if missing
            if "depreciation_amortization" not in inc and "depreciation_amortization_cf" in cf:
                inc["depreciation_amortization"] = cf["depreciation_amortization_cf"]

            # gross_profit fallback
            if "gross_profit" not in inc and "revenue" in inc and "cost_of_revenue" in inc:
                inc["gross_profit"] = inc["revenue"] - inc["cost_of_revenue"]

            # operating_income fallback
            if "operating_income" not in inc:
                if "revenue" in inc and "operating_expenses" in inc:
                    inc["operating_income"] = inc["revenue"] - inc["operating_expenses"]
                elif "gross_profit" in inc:
                    rd = inc.get("research_and_development", 0)
                    sga = inc.get("selling_general_admin", 0)
                    if rd or sga:
                        inc["operating_income"] = inc["gross_profit"] - rd - sga

            # ebitda fallback
            if "ebitda" not in inc and "operating_income" in inc:
                da = inc.get("depreciation_amortization")
                if da is not None:
                    inc["ebitda"] = inc["operating_income"] + da

            # pretax_income fallback
            if "pretax_income" not in inc and "operating_income" in inc:
                other = inc.get("other_income_expense", 0)
                interest_exp = inc.get("interest_expense", 0)
                interest_inc = inc.get("interest_income", 0)
                inc["pretax_income"] = inc["operating_income"] + other - interest_exp + interest_inc

            # Update grouped dict (for cases where inc was a new dict)
            grouped["income"][period_key] = inc

        # Persist FinancialStatement rows
        count = 0
        all_period_keys: set[tuple] = set()
        for stmt_data in grouped.values():
            all_period_keys.update(stmt_data.keys())

        for period_key in sorted(all_period_keys, key=lambda x: (x[0] or '', x[1] or 0, x[2] or '')):
            period_end_str, fy, fp = period_key
            # Skip entries missing fiscal_period (DB NOT NULL constraint)
            if not fp:
                continue
            try:
                period_end_date = datetime.strptime(
                    period_end_str, "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                continue

            for stmt_type, stmt_data in grouped.items():
                data = stmt_data.get(period_key)
                if not data:
                    continue

                existing = (
                    self.db.query(FinancialStatement)
                    .filter(
                        FinancialStatement.company_id == company.id,
                        FinancialStatement.period_end == period_end_date,
                        FinancialStatement.fiscal_period == fp,
                        FinancialStatement.statement_type == stmt_type,
                    )
                    .first()
                )
                if existing is None:
                    stmt = FinancialStatement(
                        company_id=company.id,
                        statement_type=stmt_type,
                        period_end=period_end_date,
                        fiscal_year=fy,
                        fiscal_period=fp,
                        data=data,
                    )
                    self.db.add(stmt)
                else:
                    # Merge: keep existing values, overlay new
                    merged = {**(existing.data or {}), **data}
                    existing.data = merged
                    existing.fiscal_year = fy

                count += 1

        self.db.commit()
        logger.info(
            "Parsed %d financial statement rows for cik=%s", count, company.cik
        )
        return count

    # -- Public API --

    def ingest_company(self, cik: str) -> dict[str, int]:
        """Ingest all data for a single company by CIK.

        Returns a summary dict with counts of ingested records.
        """
        padded = self._pad_cik(cik)
        log = self.log_start(detail=f"cik={padded}")
        result: dict[str, int] = {"filings": 0, "statements": 0}

        try:
            # 1. Submissions (company info + filings)
            sub_url = self.SUBMISSIONS_URL.format(cik=padded)
            sub_resp = self._get(sub_url)
            submissions = sub_resp.json()

            company = self._upsert_company(submissions)
            result["filings"] = self._upsert_filings(company, submissions)

            # 2. Company facts (XBRL)
            facts_url = self.COMPANY_FACTS_URL.format(cik=padded)
            facts_resp = self._get(facts_url)
            facts_json = facts_resp.json()

            # Store raw JSON in S3 (non-fatal if S3 is unavailable)
            try:
                s3_key = f"edgar/company_facts/{padded}.json"
                self.upload_to_s3(s3_key, facts_resp.content)
            except Exception as s3_exc:
                logger.warning("S3 upload failed for cik=%s (non-fatal): %s", padded, s3_exc)

            result["statements"] = self._parse_xbrl_facts(company, facts_json)

            total = result["filings"] + result["statements"]
            self.log_end(status="success", records_processed=total)

        except requests.HTTPError as exc:
            logger.error("HTTP error for cik=%s: %s", padded, exc)
            self.log_end(
                status="failed",
                records_processed=0,
                error_message=str(exc),
            )
            raise
        except Exception as exc:
            logger.exception("Unexpected error ingesting cik=%s", padded)
            self.log_end(
                status="failed",
                records_processed=0,
                error_message=str(exc),
            )
            raise

        return result

    def ingest_bulk(self, cik_list: list[str]) -> dict[str, Any]:
        """Ingest multiple companies sequentially.

        Returns a summary with per-CIK results and overall counts.
        """
        results: dict[str, Any] = {"succeeded": [], "failed": [], "totals": {}}
        total_filings = 0
        total_statements = 0

        for cik in cik_list:
            try:
                r = self.ingest_company(cik)
                total_filings += r["filings"]
                total_statements += r["statements"]
                results["succeeded"].append(cik)
            except Exception as exc:
                logger.error("Bulk ingest failed for cik=%s: %s", cik, exc)
                results["failed"].append({"cik": cik, "error": str(exc)})

        results["totals"] = {
            "filings": total_filings,
            "statements": total_statements,
        }
        logger.info(
            "Bulk EDGAR ingest complete: %d succeeded, %d failed",
            len(results["succeeded"]),
            len(results["failed"]),
        )
        return results

    def close(self) -> None:
        """Close HTTP session and base resources."""
        self._session.close()
        super().close()
