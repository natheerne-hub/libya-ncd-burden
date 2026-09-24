"""Configuration loading and project paths."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
SNAPSHOT = DATA / "snapshot" / "who_gho_snapshot.csv"
RAW = DATA / "raw"
EXTERNAL = DATA / "external"
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
TABLES = OUTPUTS / "tables"


def load_config(path: Path | str | None = None) -> dict:
    path = Path(path) if path else ROOT / "config.yaml"
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)
