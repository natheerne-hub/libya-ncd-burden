"""Optional module for IHME Global Burden of Disease (GBD) exports.

GBD data cannot be redistributed in this repository and has no open API, so it
is downloaded by hand from the GBD Results Tool (see data/README.md) and saved
as ``data/external/gbd_libya.csv``. When the file is absent the pipeline skips
this module and says so.
"""
from __future__ import annotations

from pathlib import Path

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
