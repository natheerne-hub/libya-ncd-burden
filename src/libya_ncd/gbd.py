"""Optional module for IHME Global Burden of Disease (GBD) exports.

GBD data cannot be redistributed in this repository and has no open API, so it
is downloaded by hand from the GBD Results Tool (see data/README.md) and saved
as ``data/external/gbd_libya.csv``. When the file is absent the pipeline skips
this module and says so.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED = ["measure_name", "location_name", "sex_name", "age_name", "cause_name",
            "metric_name", "year", "val", "upper", "lower"]


def load_gbd(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    problems = validate_gbd(df)
    if problems:
        raise ValueError("GBD export failed validation: " + "; ".join(problems))
    return df


def validate_gbd(df: pd.DataFrame) -> list[str]:
    problems = []
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return [f"missing columns {missing} — export with the default GBD Results Tool layout"]
    if (df.val < 0).any():
        problems.append("negative estimates")
    if not ((df.lower <= df.val) & (df.val <= df.upper)).all():
        problems.append("estimates outside their uncertainty interval")
    if df.duplicated(["measure_name", "location_name", "sex_name", "age_name", "cause_name", "metric_name", "year"]).any():
        problems.append("duplicate rows")
    return problems


def _slice(df, measure, metric, sex="Both", age="Age-standardized"):
    return df[(df.measure_name.str.startswith(measure)) & (df.metric_name == metric)
              & (df.sex_name == sex) & (df.age_name == age)]


def top_causes(df: pd.DataFrame, year: int, n: int = 10, measure: str = "DALYs", metric: str = "Rate") -> pd.DataFrame:
    """Leading causes by age-standardised rate in one year."""
    s = _slice(df, measure, metric)
    s = s[s.year == year].sort_values("val", ascending=False).head(n)
    return s[["cause_name", "val", "lower", "upper"]].reset_index(drop=True)


def daly_composition(df: pd.DataFrame, year: int, metric: str = "Rate") -> pd.DataFrame:
    """Split DALYs into premature death (YLL) and disability (YLD) by cause."""
    yll = _slice(df, "YLLs", metric).query("year == @year").set_index("cause_name").val
    yld = _slice(df, "YLDs", metric).query("year == @year").set_index("cause_name").val
    out = pd.DataFrame({"yll": yll, "yld": yld}).dropna()
    out["daly"] = out.yll + out.yld
    out["yll_share_pct"] = 100 * out.yll / out.daly
    return out.sort_values("daly", ascending=False).reset_index()


def cause_trend(df: pd.DataFrame, cause: str, measure: str = "DALYs", metric: str = "Rate") -> pd.DataFrame:
    s = _slice(df, measure, metric)
    return s[s.cause_name == cause].sort_values("year")[["year", "val", "lower", "upper"]].reset_index(drop=True)


# --- Language-independent extraction (IDs) and economic-input derivation -----------------
# GBD Results exports carry numeric IDs alongside names; names follow the site language
# (e.g. Arabic), so everything below keys on IDs.
MEASURE_IDS = {2: "dalys", 3: "ylds", 6: "incidence"}
CAUSE_IDS = {491: "cardiovascular_diseases", 493: "ischemic_heart_disease", 494: "stroke"}
METRIC_NUMBER, AGE_ALL = 1, 22


def extract_inputs(export_path: Path, location: str = "Libya") -> pd.DataFrame:
    """Reduce a GBD Results export to the few aggregate numbers the model uses."""
    df = pd.read_csv(export_path)
    need = {"measure_id", "cause_id", "metric_id", "age_id", "sex_id", "year", "val", "lower", "upper"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"export lacks ID columns {sorted(missing)} — re-download with IDs included")
    d = df[df.measure_id.isin(MEASURE_IDS) & df.cause_id.isin(CAUSE_IDS)
           & (df.metric_id == METRIC_NUMBER) & (df.age_id == AGE_ALL) & (df.sex_id == 3)].copy()
    d["measure"] = d.measure_id.map(MEASURE_IDS)
    d["cause"] = d.cause_id.map(CAUSE_IDS)
    d.insert(0, "location", location)
    return d[["location", "cause", "measure", "year", "val", "lower", "upper"]].sort_values(
        ["cause", "measure", "year"]).reset_index(drop=True)


def derive_economic_inputs(extract: pd.DataFrame, population_30_79: float, prevalence: float,
                           rr_hypertension: float, discount_rate: float, spread_years: int,
                           year: int | None = None) -> dict:
    """Derive the CVD event rate and DALYs per event from GBD IHD + stroke estimates.

    * events   = incident IHD + incident stroke (all ages)
    * event rate in hypertensives r1: split total events between hypertensives and
      normotensives, with hypertensives at `rr_hypertension` times the risk:
          events / N = r0 · (1 + p · (RR − 1)),  r1 = RR · r0
    * DALYs per event = (IHD + stroke DALYs) / events — a steady-state approximation of
      the undiscounted lifetime burden of one event — then discounted assuming that burden
      is spread evenly over `spread_years`.
    """
    year = year or int(extract.year.max())
    x = extract[extract.year == year].set_index(["cause", "measure"])
    causes = ["ischemic_heart_disease", "stroke"]
    events = sum(x.loc[(c, "incidence"), "val"] for c in causes)
    dalys = sum(x.loc[(c, "dalys"), "val"] for c in causes)
    ylds = sum(x.loc[(c, "ylds"), "val"] for c in causes)
    r0 = (events / population_30_79) / (1 + prevalence * (rr_hypertension - 1))
    t = np.arange(1, spread_years + 1)
    discount_factor = float(np.sum(1 / (1 + discount_rate) ** t)) / spread_years
    undiscounted = dalys / events
    return {
        "year": year,
        "events": float(events),
        "dalys": float(dalys),
        "yll_share_pct": float(100 * (1 - ylds / dalys)),
        "event_rate_hypertensive": float(rr_hypertension * r0),
        "dalys_per_event_undiscounted": float(undiscounted),
        "dalys_per_event_discounted": float(undiscounted * discount_factor),
    }


# --- Level-2 cause burden (leading causes, cross-country shares, shocks over time) -------
LEVEL2_CAUSES = {
    344: "Neglected tropical diseases & malaria", 386: "Nutritional deficiencies", 410: "Neoplasms",
    491: "Cardiovascular diseases", 508: "Chronic respiratory diseases", 526: "Digestive diseases",
    542: "Neurological disorders", 558: "Mental disorders", 626: "Musculoskeletal disorders",
    640: "Other non-communicable diseases", 653: "Skin & subcutaneous diseases", 669: "Sense organ diseases",
    688: "Transport injuries", 696: "Unintentional injuries", 717: "Self-harm & interpersonal violence",
    955: "HIV/AIDS & STIs", 956: "Respiratory infections & TB", 957: "Enteric infections",
    961: "Other infectious diseases", 962: "Maternal & neonatal disorders", 973: "Substance use disorders",
    974: "Diabetes & kidney diseases",
}
LOCATION_ISO3 = {139: "DZA", 141: "EGY", 147: "LBY", 148: "MAR", 154: "TUN"}


def extract_burden(export_path: Path, focus_location_id: int = 147, comparison_years=(2022,)) -> pd.DataFrame:
    """Level-2 DALYs (number, share of all DALYs) and YLDs. Every year for the focus country;
    only `comparison_years` for the others, which keeps the committed extract small."""
    df = pd.read_csv(export_path)
    d = df[df.cause_id.isin(LEVEL2_CAUSES) & df.location_id.isin(LOCATION_ISO3)
           & (df.age_id == AGE_ALL) & (df.sex_id == 3) & df.measure_id.isin([2, 3])]
    keep = (d.location_id == focus_location_id) | d.year.isin(comparison_years)
    d = d[keep]
    w = d[d.metric_id.isin([1, 2])].pivot_table(index=["location_id", "cause_id", "year"],
                                                columns=["measure_id", "metric_id"], values="val")
    out = pd.DataFrame({
        "dalys": w[(2, 1)],
        "dalys_share_pct": 100 * w[(2, 2)],
        "ylds": w[(3, 1)],
    }).reset_index()
    out.insert(0, "iso3", out.location_id.map(LOCATION_ISO3))
    return out.drop(columns="location_id").sort_values(["iso3", "cause_id", "year"]).reset_index(drop=True)


def load_burden(path: Path) -> pd.DataFrame:
    """Read the committed level-2 extract and attach English cause names."""
    b = pd.read_csv(path)
    b.insert(1, "cause", b.cause_id.map(LEVEL2_CAUSES))
    if b.cause.isna().any():
        raise ValueError("unknown cause_id in burden extract")
    return b


def leading_causes(burden: pd.DataFrame, iso3: str, year: int, n: int = 10) -> pd.DataFrame:
    x = burden[(burden.iso3 == iso3) & (burden.year == year)].copy()
    x["ylls"] = x.dalys - x.ylds
    x["yll_share_pct"] = 100 * x.ylls / x.dalys
    return x.sort_values("dalys", ascending=False).head(n).reset_index(drop=True)


def share_matrix(burden: pd.DataFrame, year: int, causes: list[str]) -> pd.DataFrame:
    x = burden[(burden.year == year) & burden.cause.isin(causes)]
    return x.pivot_table(index="cause", columns="iso3", values="dalys_share_pct").reindex(causes)
