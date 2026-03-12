"""
XBRL Taxonomy Mapper: Maps US-GAAP XBRL tags to canonical financial field names.

SEC EDGAR XBRL data uses varying tag names across companies and filing periods.
This module provides a single source of truth for resolving those tags into
consistent canonical field names used throughout the Excella platform.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Core mapping: canonical_field -> ordered list of XBRL tag alternatives
# Order matters: first match wins when resolving facts.
# ---------------------------------------------------------------------------

XBRL_MAPPING: dict[str, list[str]] = {
    # ── Income Statement ─────────────────────────────────────────────────
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
        "SalesRevenueServicesNet",
        "RevenueNet",
        "TotalRevenuesAndOtherIncome",
        "SalesRevenueServicesGross",
    ],
    "cost_of_revenue": [
        "CostOfGoodsAndServicesSold",
        "CostOfRevenue",
        "CostOfGoodsSold",
        "CostOfServices",
        "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization",
    ],
    "gross_profit": [
        "GrossProfit",
    ],
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
        "CurrentIncomeTaxExpenseBenefit",
    ],
    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
        "NetIncomeLossAttributableToParent",
    ],
    "eps_basic": [
        "EarningsPerShareBasic",
    ],
    "eps_diluted": [
        "EarningsPerShareDiluted",
    ],
    "shares_basic": [
        "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
        "WeightedAverageNumberOfSharesOutstandingBasic",
        "CommonStockSharesOutstanding",
    ],
    "shares_diluted": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
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

    # ── Balance Sheet ─────────────────────────────────────────────────────
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
        "InventoryFinishedGoodsNetOfReserves",
        "InventoryFinishedGoods",
        "InventoryFinishedGoodsAndWorkInProcess",
    ],
    "other_current_assets": [
        "OtherAssetsCurrent",
        "PrepaidExpenseAndOtherAssetsCurrent",
    ],
    "total_current_assets": [
        "AssetsCurrent",
    ],
    "property_plant_equipment": [
        "PropertyPlantAndEquipmentNet",
        "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization",
    ],
    "goodwill": [
        "Goodwill",
    ],
    "intangible_assets": [
        "IntangibleAssetsNetExcludingGoodwill",
        "FiniteLivedIntangibleAssetsNet",
        "IndefiniteLivedIntangibleAssetsExcludingGoodwill",
    ],
    "total_assets": [
        "Assets",
    ],
    "accounts_payable": [
        "AccountsPayableCurrent",
        "AccountsPayableAndAccruedLiabilitiesCurrent",
        "AccountsPayableTradeCurrent",
    ],
    "short_term_debt": [
        "ShortTermBorrowings",
        "CommercialPaper",
        "DebtCurrent",
        "LineOfCredit",
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
    "total_current_liabilities": [
        "LiabilitiesCurrent",
    ],
    "long_term_debt": [
        "LongTermDebtNoncurrent",
        "LongTermDebt",
        "LongTermBorrowings",
        "LongTermDebtAndCapitalLeaseObligations",
        "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
    ],
    "total_liabilities": [
        "Liabilities",
    ],
    "common_stock": [
        "CommonStockValue",
        "CommonStocksIncludingAdditionalPaidInCapital",
    ],
    "retained_earnings": [
        "RetainedEarningsAccumulatedDeficit",
    ],
    "total_stockholders_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "minority_interest": [
        "MinorityInterest",
        "RedeemableNoncontrollingInterest",
        "RedeemableNoncontrollingInterestEquityCarryingAmount",
    ],
    "total_equity": [
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "StockholdersEquity",
    ],

    # ── Cash Flow Statement ───────────────────────────────────────────────
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "capital_expenditure": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "CapitalExpenditure",
        "PaymentsForCapitalImprovements",
    ],
    "acquisitions": [
        "PaymentsToAcquireBusinessesNetOfCashAcquired",
        "PaymentsToAcquireBusinessesAndInterestInAffiliates",
        "PaymentsToAcquireBusinessesGross",
    ],
    "investing_cash_flow": [
        "NetCashProvidedByUsedInInvestingActivities",
        "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations",
    ],
    "dividends_paid": [
        "PaymentsOfDividends",
        "PaymentsOfDividendsCommonStock",
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

# ---------------------------------------------------------------------------
# Statement type classification
# ---------------------------------------------------------------------------

STATEMENT_FIELDS: dict[str, list[str]] = {
    "income": [
        "revenue",
        "cost_of_revenue",
        "gross_profit",
        "research_and_development",
        "selling_general_admin",
        "operating_expenses",
        "operating_income",
        "interest_expense",
        "interest_income",
        "other_income_expense",
        "pretax_income",
        "income_tax",
        "net_income",
        "eps_basic",
        "eps_diluted",
        "shares_basic",
        "shares_diluted",
        "depreciation_amortization",
        "ebitda",
        "stock_based_compensation",
    ],
    "balance": [
        "cash_and_equivalents",
        "short_term_investments",
        "accounts_receivable",
        "inventory",
        "other_current_assets",
        "total_current_assets",
        "property_plant_equipment",
        "goodwill",
        "intangible_assets",
        "total_assets",
        "accounts_payable",
        "short_term_debt",
        "current_portion_long_term_debt",
        "other_current_liabilities",
        "total_current_liabilities",
        "long_term_debt",
        "total_liabilities",
        "common_stock",
        "retained_earnings",
        "total_stockholders_equity",
        "minority_interest",
        "total_equity",
    ],
    "cashflow": [
        "operating_cash_flow",
        "capital_expenditure",
        "acquisitions",
        "investing_cash_flow",
        "dividends_paid",
        "share_repurchase",
        "debt_issuance",
        "debt_repayment",
        "financing_cash_flow",
        "net_change_in_cash",
    ],
}

# ---------------------------------------------------------------------------
# Computed / derived fields (require post-processing after tag resolution)
# ---------------------------------------------------------------------------

COMPUTED_FIELDS: dict[str, dict] = {
    "gross_profit": {
        "formula": "revenue - cost_of_revenue",
        "operands": ["revenue", "cost_of_revenue"],
        "operation": "subtract",
        "fallback_only": True,  # only compute if not directly reported
    },
    "operating_income": {
        "formula": "revenue - operating_expenses",
        "operands": ["revenue", "operating_expenses"],
        "operation": "subtract",
        "fallback_only": True,
    },
    "ebitda": {
        "formula": "operating_income + depreciation_amortization",
        "operands": ["operating_income", "depreciation_amortization"],
        "operation": "sum",
    },
}

# ---------------------------------------------------------------------------
# Reverse index: XBRL tag -> canonical field (built once at import time)
# ---------------------------------------------------------------------------

_TAG_TO_CANONICAL: dict[str, str] = {}
for _canonical, _tags in XBRL_MAPPING.items():
    for _tag in _tags:
        # First mapping wins if a tag appears under multiple canonical fields
        if _tag not in _TAG_TO_CANONICAL:
            _TAG_TO_CANONICAL[_tag] = _canonical

# Which statement type each canonical field belongs to (reverse of STATEMENT_FIELDS)
_FIELD_TO_STATEMENT: dict[str, str] = {}
for _stmt_type, _fields in STATEMENT_FIELDS.items():
    for _field in _fields:
        _FIELD_TO_STATEMENT[_field] = _stmt_type


def get_canonical_field(xbrl_tag: str) -> str | None:
    """Return the canonical field name for a given XBRL tag, or None."""
    return _TAG_TO_CANONICAL.get(xbrl_tag)


def get_statement_type(canonical_field: str) -> str | None:
    """Return which statement type a canonical field belongs to."""
    return _FIELD_TO_STATEMENT.get(canonical_field)


def resolve_xbrl_facts(facts: dict[str, object], statement_type: str) -> dict[str, object]:
    """Resolve a dict of {xbrl_tag: value} into {canonical_field: value}.

    For each canonical field that belongs to *statement_type*, scan the ordered
    list of XBRL tag alternatives and pick the first one present in *facts*.

    After direct resolution, compute any derived fields whose operands are
    available.

    Args:
        facts: Mapping of raw XBRL tag names to numeric values.
        statement_type: One of "income", "balance", "cashflow".

    Returns:
        Dict of canonical field names to values for the requested statement type.
    """
    if statement_type not in STATEMENT_FIELDS:
        raise ValueError(f"Unknown statement_type: {statement_type!r}. "
                         f"Expected one of {list(STATEMENT_FIELDS)}")

    target_fields = STATEMENT_FIELDS[statement_type]
    resolved: dict[str, object] = {}

    # Direct resolution: walk each canonical field and try alternatives in order
    for field in target_fields:
        if field in COMPUTED_FIELDS:
            continue  # handle after direct resolution
        alternatives = XBRL_MAPPING.get(field, [])
        for tag in alternatives:
            if tag in facts and facts[tag] is not None:
                resolved[field] = facts[tag]
                break

    # Computed fields
    for field in target_fields:
        if field not in COMPUTED_FIELDS:
            continue
        spec = COMPUTED_FIELDS[field]

        # If already resolved directly and this is a fallback-only computation, skip
        if spec.get("fallback_only") and field in resolved:
            continue

        operands = [resolved.get(op) for op in spec["operands"]]
        if any(v is None for v in operands):
            continue  # cannot compute without all operands

        if spec["operation"] == "sum":
            resolved[field] = sum(operands)  # type: ignore[arg-type]
        elif spec["operation"] == "subtract":
            resolved[field] = operands[0] - operands[1]  # type: ignore[operator]

    return resolved
