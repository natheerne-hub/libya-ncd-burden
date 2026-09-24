"""Data acquisition (WHO GHO OData API) and tidying.

The pipeline works in two modes:
* ``fetch``    — pull the latest values from the WHO GHO API into ``data/raw/``;
* ``snapshot`` — use the version-controlled snapshot in ``data/snapshot/`` so the
  analysis is reproducible offline and in CI.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from .config import RAW, SNAPSHOT

TIDY_COLUMNS = ["indicator_code", "iso3", "year", "sex", "value", "low", "high"]
SEX_MAP = {"SEX_BTSX": "both", "SEX_MLE": "male", "SEX_FMLE": "female", None: "both", "": "both"}


def _gho_url(base_url: str, code: str, iso3: list[str]) -> str:
    countries = ",".join(f"'{c}'" for c in iso3)
    flt = urllib.parse.quote(f"SpatialDim in ({countries})")
    return f"{base_url}/{code}?$filter={flt}"


def tidy_gho_records(records: list[dict], code: str, age_group: str | None) -> pd.DataFrame:
    """Convert raw GHO OData records into the tidy schema.

    Keeps only the configured overall age band (GHO stores some indicators
    split by age in ``Dim2``) and drops records without a numeric value.
    """
    rows = []
    for rec in records:
        if rec.get("NumericValue") is None:
            continue
        dim2 = rec.get("Dim2") or None
        if dim2 != age_group:
            continue
        rows.append(
            {
                "indicator_code": code,
                "iso3": rec["SpatialDim"],
                "year": int(rec["TimeDim"]),
                "sex": SEX_MAP.get(rec.get("Dim1"), rec.get("Dim1")),
                "value": float(rec["NumericValue"]),
                "low": rec.get("Low"),
                "high": rec.get("High"),
            }
        )
    return pd.DataFrame(rows, columns=TIDY_COLUMNS)


def fetch_who_gho(cfg: dict, out_path: Path | None = None, timeout: int = 60) -> pd.DataFrame:
    """Download every configured indicator for every configured country."""
    base = cfg["who_gho"]["base_url"]
    iso3 = list(cfg["countries"])
    frames = []
    for code, meta in cfg["who_gho"]["indicators"].items():
        url = _gho_url(base, code, iso3)
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (fixed https host)
            payload = json.load(resp)
        frame = tidy_gho_records(payload.get("value", []), code, meta.get("age_group"))
        print(f"  {code:<32} {len(frame):>5} rows")
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True).sort_values(["indicator_code", "iso3", "sex", "year"])
    out_path = out_path or RAW / "who_gho_latest.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


def load_who(path: Path | None = None) -> pd.DataFrame:
    """Load tidy WHO data (latest fetch if present, otherwise the snapshot)."""
    if path is None:
        latest = RAW / "who_gho_latest.csv"
        path = latest if latest.exists() else SNAPSHOT
    df = pd.read_csv(path)
    missing = set(TIDY_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    df.attrs["source_path"] = str(path)
    return df


def validate_who(df: pd.DataFrame, cfg: dict) -> list[str]:
    """Return a list of data-quality problems (empty list = clean)."""
    problems: list[str] = []
    if df.duplicated(["indicator_code", "iso3", "year", "sex"]).any():
        problems.append("duplicate indicator/country/year/sex rows")
    pct = [c for c in cfg["who_gho"]["indicators"] if "_pc_" not in c]
    out_of_range = df[df.indicator_code.isin(pct) & ~df.value.between(0, 100)]
    if len(out_of_range):
        problems.append(f"{len(out_of_range)} percentage values outside 0–100")
    has_ci = df.low.notna() & df.high.notna()
    bad_ci = df[has_ci & ~((df.low <= df.value) & (df.value <= df.high))]
    if len(bad_ci):
        problems.append(f"{len(bad_ci)} rows where value lies outside its uncertainty interval")
    unknown = set(df.iso3) - set(cfg["countries"])
    if unknown:
        problems.append(f"unexpected countries: {sorted(unknown)}")
    return problems


def series(df: pd.DataFrame, code: str, iso3: str, sex: str = "both", max_year: int | None = None) -> pd.DataFrame:
    """One indicator/country/sex time series, sorted by year."""
    out = df[(df.indicator_code == code) & (df.iso3 == iso3) & (df.sex == sex)]
    if max_year is not None:
        out = out[out.year <= max_year]
    return out.sort_values("year").reset_index(drop=True)
