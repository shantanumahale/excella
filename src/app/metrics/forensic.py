"""Forensic accounting metrics: Altman Z-Score, Piotroski F-Score, Beneish M-Score."""

from __future__ import annotations


def _safe_div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def _growth(current, prior):
    """Compute growth rate: (current - prior) / abs(prior)."""
    if current is None or prior is None or prior == 0:
        return None
    return (current - prior) / abs(prior)


def _altman_z_score(income: dict, balance: dict, market_cap: float | None) -> dict:
    """Compute Altman Z-Score and its components."""
    total_assets = balance.get("total_assets")
    total_current_assets = balance.get("total_current_assets")
    total_current_liabilities = balance.get("total_current_liabilities")
    retained_earnings = balance.get("retained_earnings")
    total_liabilities = balance.get("total_liabilities")
    total_equity = balance.get("total_stockholders_equity") or balance.get("total_equity")

    # Fallback: compute total_liabilities from total_assets - total_equity
    if total_liabilities is None and total_assets is not None and total_equity is not None:
        total_liabilities = total_assets - total_equity

    revenue = income.get("revenue")
    operating_income = income.get("operating_income")  # proxy for EBIT

    # operating_income fallback
    if operating_income is None and revenue is not None:
        opex = income.get("operating_expenses")
        gp = income.get("gross_profit")
        cogs = income.get("cost_of_revenue")
        if opex is not None:
            operating_income = revenue - opex
        elif gp is not None or cogs is not None:
            if gp is None and cogs is not None:
                gp = revenue - cogs
            if gp is not None:
                rd = income.get("research_and_development", 0)
                sga = income.get("selling_general_admin", 0)
                if rd or sga:
                    operating_income = gp - rd - sga

    if total_assets is None or total_assets == 0:
        return {"altman_z_score": None, "altman_z_components": None, "z_score_zone": None}

    # NWC / TA
    nwc = None
    if total_current_assets is not None and total_current_liabilities is not None:
        nwc = total_current_assets - total_current_liabilities
    x1 = _safe_div(nwc, total_assets)

    # RE / TA
    x2 = _safe_div(retained_earnings, total_assets)

    # EBIT / TA
    x3 = _safe_div(operating_income, total_assets)

    # Market equity / TL — use market_cap if available, else total_equity as proxy
    equity_proxy = market_cap if market_cap is not None else total_equity
    x4 = _safe_div(equity_proxy, total_liabilities)

    # Revenue / TA
    x5 = _safe_div(revenue, total_assets)

    components = {"x1_nwc_ta": x1, "x2_re_ta": x2, "x3_ebit_ta": x3, "x4_equity_tl": x4, "x5_rev_ta": x5}

    z_score = None
    if all(v is not None for v in [x1, x2, x3, x4, x5]):
        z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5

    zone = None
    if z_score is not None:
        if z_score < 1.81:
            zone = "distress"
        elif z_score < 2.99:
            zone = "grey"
        else:
            zone = "safe"

    return {"altman_z_score": z_score, "altman_z_components": components, "z_score_zone": zone}


def _piotroski_f_score(
    income: dict, balance: dict, cashflow: dict,
    prior_income: dict, prior_balance: dict, prior_cashflow: dict,
) -> dict:
    """Compute Piotroski F-Score (0-9)."""
    net_income = income.get("net_income")
    total_assets = balance.get("total_assets")
    operating_cash_flow = cashflow.get("operating_cash_flow")
    total_current_assets = balance.get("total_current_assets")
    total_current_liabilities = balance.get("total_current_liabilities")
    long_term_debt = balance.get("long_term_debt")
    gross_profit = income.get("gross_profit")
    revenue = income.get("revenue")
    shares_diluted = income.get("shares_diluted")

    # gross_profit fallback
    if gross_profit is None and revenue is not None:
        cogs = income.get("cost_of_revenue")
        if cogs is not None:
            gross_profit = revenue - cogs

    prior_total_assets = prior_balance.get("total_assets")
    prior_net_income = prior_income.get("net_income")
    prior_long_term_debt = prior_balance.get("long_term_debt")
    prior_total_current_assets = prior_balance.get("total_current_assets")
    prior_total_current_liabilities = prior_balance.get("total_current_liabilities")
    prior_gross_profit = prior_income.get("gross_profit")
    prior_revenue = prior_income.get("revenue")
    prior_shares_diluted = prior_income.get("shares_diluted")

    # prior gross_profit fallback
    if prior_gross_profit is None and prior_revenue is not None:
        prior_cogs = prior_income.get("cost_of_revenue")
        if prior_cogs is not None:
            prior_gross_profit = prior_revenue - prior_cogs

    signals = {}
    score = 0

    # 1. ROA > 0
    roa = _safe_div(net_income, total_assets)
    signals["roa_positive"] = roa is not None and roa > 0
    if signals["roa_positive"]:
        score += 1

    # 2. OCF > 0
    signals["ocf_positive"] = operating_cash_flow is not None and operating_cash_flow > 0
    if signals["ocf_positive"]:
        score += 1

    # 3. ROA increasing
    prior_roa = _safe_div(prior_net_income, prior_total_assets)
    signals["roa_increasing"] = roa is not None and prior_roa is not None and roa > prior_roa
    if signals["roa_increasing"]:
        score += 1

    # 4. Accruals: OCF > net income
    signals["ocf_exceeds_net_income"] = (
        operating_cash_flow is not None and net_income is not None and operating_cash_flow > net_income
    )
    if signals["ocf_exceeds_net_income"]:
        score += 1

    # 5. Long-term debt ratio decreasing
    ltd_ratio = _safe_div(long_term_debt, total_assets)
    prior_ltd_ratio = _safe_div(prior_long_term_debt, prior_total_assets)
    signals["leverage_decreasing"] = (
        ltd_ratio is not None and prior_ltd_ratio is not None and ltd_ratio < prior_ltd_ratio
    )
    if signals["leverage_decreasing"]:
        score += 1

    # 6. Current ratio increasing
    cr = _safe_div(total_current_assets, total_current_liabilities)
    prior_cr = _safe_div(prior_total_current_assets, prior_total_current_liabilities)
    signals["current_ratio_increasing"] = cr is not None and prior_cr is not None and cr > prior_cr
    if signals["current_ratio_increasing"]:
        score += 1

    # 7. No new share dilution
    signals["no_dilution"] = (
        shares_diluted is not None and prior_shares_diluted is not None and shares_diluted <= prior_shares_diluted
    )
    if signals["no_dilution"]:
        score += 1

    # 8. Gross margin increasing
    gm = _safe_div(gross_profit, revenue)
    prior_gm = _safe_div(prior_gross_profit, prior_revenue)
    signals["gross_margin_increasing"] = gm is not None and prior_gm is not None and gm > prior_gm
    if signals["gross_margin_increasing"]:
        score += 1

    # 9. Asset turnover increasing
    at = _safe_div(revenue, total_assets)
    prior_at = _safe_div(prior_revenue, prior_total_assets)
    signals["asset_turnover_increasing"] = at is not None and prior_at is not None and at > prior_at
    if signals["asset_turnover_increasing"]:
        score += 1

    strength = None
    if score >= 7:
        strength = "strong"
    elif score >= 4:
        strength = "moderate"
    else:
        strength = "weak"

    return {"piotroski_f_score": score, "piotroski_signals": signals, "piotroski_strength": strength}


def _beneish_m_score(
    income: dict, balance: dict, cashflow: dict,
    prior_income: dict, prior_balance: dict,
) -> dict:
    """Compute Beneish M-Score and its component indices."""
    revenue = income.get("revenue")
    gross_profit = income.get("gross_profit")
    net_income = income.get("net_income")
    operating_cash_flow = cashflow.get("operating_cash_flow")
    accounts_receivable = balance.get("accounts_receivable")
    total_current_assets = balance.get("total_current_assets")
    property_plant_equipment = balance.get("property_plant_equipment")
    total_assets = balance.get("total_assets")
    depreciation_amortization = income.get("depreciation_amortization")
    selling_general_admin = income.get("selling_general_admin")
    total_current_liabilities = balance.get("total_current_liabilities")
    long_term_debt = balance.get("long_term_debt")
    total_liabilities = balance.get("total_liabilities")

    # gross_profit fallback
    if gross_profit is None and revenue is not None:
        cogs = income.get("cost_of_revenue")
        if cogs is not None:
            gross_profit = revenue - cogs

    # total_liabilities fallback
    if total_liabilities is None and total_assets is not None:
        te = balance.get("total_stockholders_equity") or balance.get("total_equity")
        if te is not None:
            total_liabilities = total_assets - te

    p_revenue = prior_income.get("revenue")
    p_gross_profit = prior_income.get("gross_profit")
    # prior gross_profit fallback
    if p_gross_profit is None and p_revenue is not None:
        p_cogs = prior_income.get("cost_of_revenue")
        if p_cogs is not None:
            p_gross_profit = p_revenue - p_cogs
    p_accounts_receivable = prior_balance.get("accounts_receivable")
    p_total_current_assets = prior_balance.get("total_current_assets")
    p_property_plant_equipment = prior_balance.get("property_plant_equipment")
    p_total_assets = prior_balance.get("total_assets")
    p_depreciation_amortization = prior_income.get("depreciation_amortization")
    p_selling_general_admin = prior_income.get("selling_general_admin")
    p_total_liabilities = prior_balance.get("total_liabilities")
    # prior total_liabilities fallback
    if p_total_liabilities is None and p_total_assets is not None:
        p_te = prior_balance.get("total_stockholders_equity") or prior_balance.get("total_equity")
        if p_te is not None:
            p_total_liabilities = p_total_assets - p_te

    # DSRI = (receivables/revenue)_t / (receivables/revenue)_{t-1}
    dsri = _safe_div(_safe_div(accounts_receivable, revenue), _safe_div(p_accounts_receivable, p_revenue))

    # GMI = gross_margin_{t-1} / gross_margin_t
    gm_current = _safe_div(gross_profit, revenue)
    gm_prior = _safe_div(p_gross_profit, p_revenue)
    gmi = _safe_div(gm_prior, gm_current)

    # AQI = (1 - (CA+PPE)/TA)_t / (1 - (CA+PPE)/TA)_{t-1}
    def _asset_quality(ca, ppe, ta):
        if ca is None or ppe is None or ta is None or ta == 0:
            return None
        return 1 - (ca + ppe) / ta

    aq_current = _asset_quality(total_current_assets, property_plant_equipment, total_assets)
    aq_prior = _asset_quality(p_total_current_assets, p_property_plant_equipment, p_total_assets)
    aqi = _safe_div(aq_current, aq_prior)

    # SGI = revenue_t / revenue_{t-1}
    sgi = _safe_div(revenue, p_revenue)

    # DEPI = depreciation_rate_{t-1} / depreciation_rate_t
    # depreciation_rate = D&A / (D&A + PPE)
    def _dep_rate(da, ppe):
        if da is None or ppe is None:
            return None
        denom = da + ppe
        return _safe_div(da, denom)

    dr_current = _dep_rate(depreciation_amortization, property_plant_equipment)
    dr_prior = _dep_rate(p_depreciation_amortization, p_property_plant_equipment)
    depi = _safe_div(dr_prior, dr_current)

    # SGAI = (SGA/revenue)_t / (SGA/revenue)_{t-1}
    sgai = _safe_div(_safe_div(selling_general_admin, revenue), _safe_div(p_selling_general_admin, p_revenue))

    # LVGI = leverage_t / leverage_{t-1}
    lev_current = _safe_div(total_liabilities, total_assets)
    lev_prior = _safe_div(p_total_liabilities, p_total_assets)
    lvgi = _safe_div(lev_current, lev_prior)

    # TATA = (net_income - OCF) / total_assets
    tata = None
    if net_income is not None and operating_cash_flow is not None and total_assets is not None and total_assets != 0:
        tata = (net_income - operating_cash_flow) / total_assets

    components = {
        "dsri": dsri, "gmi": gmi, "aqi": aqi, "sgi": sgi,
        "depi": depi, "sgai": sgai, "lvgi": lvgi, "tata": tata,
    }

    # M-Score = -4.84 + 0.92*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
    #           + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
    m_score = None
    if all(v is not None for v in components.values()):
        m_score = (
            -4.84
            + 0.92 * dsri
            + 0.528 * gmi
            + 0.404 * aqi
            + 0.892 * sgi
            + 0.115 * depi
            - 0.172 * sgai
            + 4.679 * tata
            - 0.327 * lvgi
        )

    manipulation_risk = None
    if m_score is not None:
        manipulation_risk = m_score > -1.78

    return {
        "beneish_m_score": m_score,
        "beneish_components": components,
        "manipulation_risk": manipulation_risk,
    }


def compute(
    income: dict,
    balance: dict,
    cashflow: dict,
    prior_income: dict | None = None,
    prior_balance: dict | None = None,
    prior_cashflow: dict | None = None,
    market_cap: float | None = None,
) -> dict:
    """Compute forensic accounting metrics.

    Returns a dict containing Altman Z-Score, Piotroski F-Score,
    Beneish M-Score, their components, and risk flags.
    """
    prior_income = prior_income or {}
    prior_balance = prior_balance or {}
    prior_cashflow = prior_cashflow or {}

    result = {}

    # Altman Z-Score
    z_data = _altman_z_score(income, balance, market_cap)
    result.update(z_data)

    # Piotroski F-Score
    f_data = _piotroski_f_score(income, balance, cashflow, prior_income, prior_balance, prior_cashflow)
    result.update(f_data)

    # Beneish M-Score
    m_data = _beneish_m_score(income, balance, cashflow, prior_income, prior_balance)
    result.update(m_data)

    # Consolidated risk flags
    result["risk_flags"] = {
        "z_score_distress": z_data.get("z_score_zone") == "distress",
        "manipulation_risk": m_data.get("manipulation_risk", False),
        "piotroski_weak": f_data.get("piotroski_f_score", 0) < 4,
        "piotroski_strong": f_data.get("piotroski_f_score", 0) >= 7,
    }

    return result
