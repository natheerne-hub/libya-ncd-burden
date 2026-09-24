"""Health-economic scenario model: scaling up hypertension control.

A deliberately transparent, cohort-level model (not a Markov model):

    hypertensives          N  = population_30_79 × prevalence
    additional controlled  ΔC = N × (target_control − current_control)
    annual programme cost      = ΔC × (drug & follow-up + programme overhead)
    CVD events averted / year  = ΔC × baseline event rate × relative risk reduction
    cost offsets / year        = events averted × cost per event
    DALYs averted / year       = events averted × DALYs per event

Costs and DALYs are discounted over the horizon. The incremental cost-
effectiveness ratio (ICER) is net cost per DALY averted and is judged against
multiples of GDP per capita — a convention that is widely used but also widely
criticised (see docs/ECONOMIC_MODEL.md); the cost-effectiveness acceptability
curve (CEAC) shows the full range rather than a single threshold.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

PARAM_NAMES = [
    "population_30_79",
    "annual_cost_per_controlled_patient",
    "programme_cost_per_additional_patient",
    "baseline_cvd_event_rate_uncontrolled",
    "relative_risk_reduction_if_controlled",
    "cost_per_cvd_event",
    "dalys_per_cvd_event",
]


@dataclass
class Inputs:
    prevalence: float            # proportion of adults 30–79 with hypertension (data)
    current_control: float       # proportion of hypertensives controlled (data)
    target_control: float
    horizon_years: int
    discount_rate: float
    population_30_79: float
    annual_cost_per_controlled_patient: float
    programme_cost_per_additional_patient: float
    baseline_cvd_event_rate_uncontrolled: float
    relative_risk_reduction_if_controlled: float
    cost_per_cvd_event: float
    dalys_per_cvd_event: float


def annuity_factor(rate: float, years: int) -> float:
    """Present value of 1 received at the end of each year for `years` years."""
    t = np.arange(1, years + 1)
    return float(np.sum(1 / (1 + rate) ** t))


def run_model(x: Inputs) -> dict:
    if not 0 <= x.current_control <= 1 or not 0 <= x.target_control <= 1:
        raise ValueError("control rates must be proportions in [0, 1]")
    hypertensives = x.population_30_79 * x.prevalence
    additional = hypertensives * max(0.0, x.target_control - x.current_control)
    af = annuity_factor(x.discount_rate, x.horizon_years)

    annual_cost = additional * (x.annual_cost_per_controlled_patient + x.programme_cost_per_additional_patient)
    annual_events_averted = additional * x.baseline_cvd_event_rate_uncontrolled * x.relative_risk_reduction_if_controlled
    annual_offsets = annual_events_averted * x.cost_per_cvd_event
    annual_dalys = annual_events_averted * x.dalys_per_cvd_event

    cost = annual_cost * af
    offsets = annual_offsets * af
    dalys = annual_dalys * af
    net = cost - offsets
    return {
        "hypertensives": hypertensives,
        "additional_controlled": additional,
        "gross_cost": cost,
        "cost_offsets": offsets,
        "net_cost": net,
        "events_averted": annual_events_averted * x.horizon_years,  # undiscounted count
        "dalys_averted": dalys,
        "icer_per_daly": net / dalys if dalys > 0 else float("nan"),
        "cost_per_event_averted": net / (annual_events_averted * af) if annual_events_averted > 0 else float("nan"),
    }


def build_inputs(cfg: dict, prevalence: float, current_control: float, overrides: dict | None = None) -> Inputs:
    e = cfg["economics"]
    values = {k: float(e["params"][k]["value"]) for k in PARAM_NAMES}
    values.update(overrides or {})
    return Inputs(
        prevalence=prevalence,
        current_control=current_control,
        target_control=float(e["target_control_rate"]),
        horizon_years=int(e["horizon_years"]),
        discount_rate=float(e["discount_rate"]),
        **values,
    )


def one_way_sensitivity(cfg: dict, prevalence: float, current_control: float, swing: float = 0.25) -> pd.DataFrame:
    """ICER at ±`swing` of each parameter (tornado diagram input)."""
    base = run_model(build_inputs(cfg, prevalence, current_control))["icer_per_daly"]
    rows = []
    for name in PARAM_NAMES:
        v = float(cfg["economics"]["params"][name]["value"])
        lo = run_model(build_inputs(cfg, prevalence, current_control, {name: v * (1 - swing)}))["icer_per_daly"]
        hi = run_model(build_inputs(cfg, prevalence, current_control, {name: v * (1 + swing)}))["icer_per_daly"]
        rows.append({"parameter": name, "icer_low_input": lo, "icer_high_input": hi,
                     "range": abs(hi - lo), "base_icer": base,
                     "source": cfg["economics"]["params"][name]["source"]})
    return pd.DataFrame(rows).sort_values("range", ascending=False).reset_index(drop=True)


# --- Probabilistic sensitivity analysis ------------------------------------

def _draw(rng: np.random.Generator, mean: float, dist: dict, n: int) -> np.ndarray:
    kind = dist["type"]
    if kind == "normal":
        return np.clip(rng.normal(mean, dist["sd"], n), 1e-9, None)
    if kind == "gamma":  # parameterised by mean and coefficient of variation
        shape = 1 / dist["cv"] ** 2
        return rng.gamma(shape, mean / shape, n)
    if kind == "beta":   # method of moments from mean and sd
        return beta_draw(rng, mean, dist["sd"], n)
    raise ValueError(f"unknown distribution {kind!r}")


def beta_draw(rng: np.random.Generator, mean: float, sd: float, n: int) -> np.ndarray:
    var = sd ** 2
    if not 0 < mean < 1 or var >= mean * (1 - mean):
        raise ValueError("beta needs 0 < mean < 1 and sd² < mean·(1−mean)")
    k = mean * (1 - mean) / var - 1
    return rng.beta(mean * k, (1 - mean) * k, n)


def ci_to_sd(low: float, high: float) -> float:
    """Approximate SD from a 95% uncertainty interval."""
    return (high - low) / (2 * 1.96)


def probabilistic_sensitivity(cfg: dict, prevalence: tuple[float, float], current_control: tuple[float, float]) -> pd.DataFrame:
    """Monte-Carlo PSA. `prevalence` / `current_control` are (mean, sd) as proportions,
    so the WHO uncertainty intervals propagate into the economic result."""
    e = cfg["economics"]
    n = int(e["psa_iterations"])
    rng = np.random.default_rng(int(e["random_seed"]))
    draws = {k: _draw(rng, float(e["params"][k]["value"]), e["params"][k]["dist"], n) for k in PARAM_NAMES}
    draws["prevalence"] = beta_draw(rng, *prevalence, n)
    draws["current_control"] = beta_draw(rng, *current_control, n)
    rows = []
    for i in range(n):
        x = Inputs(
            prevalence=draws["prevalence"][i],
            current_control=draws["current_control"][i],
            target_control=float(e["target_control_rate"]),
            horizon_years=int(e["horizon_years"]),
            discount_rate=float(e["discount_rate"]),
            **{k: draws[k][i] for k in PARAM_NAMES},
        )
        r = run_model(x)
        rows.append({"net_cost": r["net_cost"], "dalys_averted": r["dalys_averted"], "icer_per_daly": r["icer_per_daly"]})
    return pd.DataFrame(rows)


def ceac(psa: pd.DataFrame, wtp_grid: np.ndarray) -> pd.DataFrame:
    """Probability the scale-up is cost-effective (net monetary benefit > 0) at each WTP."""
    probs = [float(((w * psa.dalys_averted - psa.net_cost) > 0).mean()) for w in wtp_grid]
    return pd.DataFrame({"wtp_per_daly": wtp_grid, "prob_cost_effective": probs})
