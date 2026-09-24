"""Descriptive epidemiology and health-financing metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import series


def aarc(years, values) -> float:
    """Average annual rate of change from a log-linear fit: ln(y) = a + b·t → e^b − 1.

    Uses every point in the window (more robust than a two-point CAGR).
    """
    years = np.asarray(years, dtype=float)
    values = np.asarray(values, dtype=float)
    mask = np.isfinite(values) & (values > 0)
    if mask.sum() < 2:
        return float("nan")
    slope = np.polyfit(years[mask], np.log(values[mask]), 1)[0]
    return float(np.expm1(slope))


def window_aarc(s: pd.DataFrame, start: int, end: int) -> float:
    w = s[(s.year >= start) & (s.year <= end)]
    return aarc(w.year, w.value)


def sdg_34_progress(s: pd.DataFrame, baseline_year: int = 2015, target_year: int = 2030,
                    relative_reduction: float = 1 / 3) -> dict:
    """Assess progress toward SDG 3.4 (one-third reduction in premature NCD mortality)."""
    base = s.loc[s.year == baseline_year, "value"]
    if base.empty:
        raise ValueError(f"no value for baseline year {baseline_year}")
    base = float(base.iloc[0])
    latest = s.iloc[-1]
    latest_year, latest_value = int(latest.year), float(latest.value)
    target = base * (1 - relative_reduction)
    trend = window_aarc(s, baseline_year, latest_year)
    years_left = target_year - latest_year
    projected = latest_value * (1 + trend) ** years_left
    required = (target / latest_value) ** (1 / years_left) - 1
    return {
        "baseline_year": baseline_year,
        "baseline_value": base,
        "latest_year": latest_year,
        "latest_value": latest_value,
        "target_value": target,
        "observed_aarc": trend,
        "required_aarc": required,
        "projected_target_year_value": projected,
        "on_track": bool(projected <= target),
    }


def latest(df: pd.DataFrame, code: str, iso3: str, sex: str = "both", max_year: int | None = None) -> pd.Series:
    s = series(df, code, iso3, sex, max_year)
    if s.empty:
        raise ValueError(f"no data for {code} / {iso3} / {sex}")
    return s.iloc[-1]


def comparison_table(df: pd.DataFrame, cfg: dict, codes: list[str]) -> pd.DataFrame:
    """Latest value, change since 2000 and AARC for each country × indicator."""
    rows = []
    max_year = cfg.get("max_observed_year")
    for code in codes:
        for iso3, name in cfg["countries"].items():
            s = series(df, code, iso3, max_year=max_year)
            if s.empty:
                continue
            first, last = s.iloc[0], s.iloc[-1]
            rows.append({
                "indicator_code": code,
                "indicator": cfg["who_gho"]["indicators"][code]["short"],
                "iso3": iso3,
                "country": name,
                "first_year": int(first.year),
                "first_value": float(first.value),
                "latest_year": int(last.year),
                "latest_value": float(last.value),
                "latest_low": last.low,
                "latest_high": last.high,
                "abs_change": float(last.value - first.value),
                "aarc_pct": 100 * aarc(s.year, s.value),
            })
    out = pd.DataFrame(rows)
    out["rank_high_is_1"] = out.groupby("indicator_code")["latest_value"].rank(ascending=False, method="min").astype(int)
    return out


def hypertension_cascade(df: pd.DataFrame, iso3: str, year: int | None = None) -> dict:
    """Care cascade among adults 30–79 with hypertension (all shares in %).

    WHO reports diagnosis/treatment/control as % of *all* hypertensives, so the
    losses between steps can be read directly.
    """
    codes = {
        "prevalence": "NCD_HYP_PREVALENCE_A",
        "diagnosed": "NCD_HYP_DIAGNOSIS_A",
        "treated": "NCD_HYP_TREATMENT_A",
        "controlled": "NCD_HYP_CONTROL_A",
    }
    out: dict = {"iso3": iso3}
    common_years = None
    for code in codes.values():
        yrs = set(series(df, code, iso3).year)
        common_years = yrs if common_years is None else common_years & yrs
    if not common_years:
        raise ValueError(f"no common cascade year for {iso3}")
    year = year or max(common_years)
    out["year"] = year
    for key, code in codes.items():
        s = series(df, code, iso3)
        out[key] = float(s.loc[s.year == year, "value"].iloc[0])
    out["undiagnosed"] = 100 - out["diagnosed"]
    out["diagnosed_not_treated"] = out["diagnosed"] - out["treated"]
    out["treated_not_controlled"] = out["treated"] - out["controlled"]
    return out


def financing_profile(df: pd.DataFrame, iso3: str) -> dict:
    """Level, trend and volatility of health spending."""
    che_pc = series(df, "GHED_CHE_pc_US_SHA2011", iso3)
    che_gdp = series(df, "GHED_CHEGDP_SHA2011", iso3)
    gov_pc = series(df, "GHED_GGHE-D_pc_US_SHA2011", iso3)
    oop = series(df, "GHED_OOPSCHE_SHA2011", iso3)
    yoy = che_pc.value.pct_change().dropna()
    last_year = int(che_pc.year.iloc[-1])
    last_che_pc = float(che_pc.value.iloc[-1])
    last_che_gdp = float(che_gdp.loc[che_gdp.year == last_year, "value"].iloc[0])
    last_gov = float(gov_pc.loc[gov_pc.year == last_year, "value"].iloc[0])
    return {
        "iso3": iso3,
        "latest_year": last_year,
        "che_per_capita_usd": last_che_pc,
        "che_pct_gdp": last_che_gdp,
        "gov_share_of_che_pct": 100 * last_gov / last_che_pc,
        "oop_share_pct": float(oop.value.iloc[-1]),
        "oop_share_first": float(oop.value.iloc[0]),
        "che_pc_aarc_pct": 100 * aarc(che_pc.year, che_pc.value),
        # Volatility: SD of year-on-year % change in per-capita spend.
        "che_pc_volatility_pct": 100 * float(yoy.std()),
        # GDP per capita implied by WHO's own two series (CHE per capita ÷ CHE share of GDP).
        "implied_gdp_per_capita_usd": last_che_pc / (last_che_gdp / 100),
    }
