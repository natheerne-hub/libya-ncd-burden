"""Static figures (PNG) for the README and report.

Design: focus + context. Libya is the one saturated series; comparator
countries are recessive gray and directly labelled, so identity never relies
on colour alone. Palette validated for colour-vision deficiency.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .data import series  # noqa: E402

FOCUS = "#2a78d6"
SECOND = "#eb6834"
CONTEXT = "#a3a29c"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"
CASCADE = {"controlled": "#104281", "treated_not_controlled": "#2a78d6",
           "diagnosed_not_treated": "#86b6ef", "undiagnosed": "#dcdbd5"}

SOURCE_NOTE = "Source: WHO Global Health Observatory."
PARAM_LABELS = {
    "population_30_79": "Population aged 30–79",
    "annual_cost_per_controlled_patient": "Treatment cost per patient-year",
    "programme_cost_per_additional_patient": "Programme cost per new patient",
    "baseline_cvd_event_rate_uncontrolled": "CVD event rate if uncontrolled",
    "relative_risk_reduction_if_controlled": "Risk reduction if controlled",
    "cost_per_cvd_event": "Cost per CVD event",
    "dalys_per_cvd_event": "DALYs lost per CVD event",
}


def _style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
        "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "font.size": 10, "font.family": "DejaVu Sans", "lines.linewidth": 2, "legend.frameon": False,
    })


def _finish(fig, path: Path, note: str = SOURCE_NOTE):
    fig.text(0.01, 0.01, note, fontsize=8, color=MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.035 * (1 + note.count("\n")), 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def _end_labels(ax, items, min_gap_frac=0.055):
    """Place end-of-line labels, nudging them apart so none overlap.

    items: list of (text, x, y, bold)."""
    if not items:
        return
    lo, hi = ax.get_ylim()
    gap = (hi - lo) * min_gap_frac
    items = sorted(items, key=lambda it: it[2])
    ys = [it[2] for it in items]
    for i in range(1, len(ys)):          # push up
        ys[i] = max(ys[i], ys[i - 1] + gap)
    shift = max(0.0, ys[-1] - (hi - gap / 2))
    ys = [y - shift for y in ys]         # keep inside the axes
    for i in range(len(ys) - 2, -1, -1):  # re-resolve after shifting down
        ys[i] = min(ys[i], ys[i + 1] - gap)
    for (text, x, _y, bold), y in zip(items, ys):
        ax.annotate(text, (x, y), xytext=(5, 0), textcoords="offset points", va="center",
                    fontsize=9 if bold else 8, fontweight="bold" if bold else "normal",
                    color=INK if bold else INK_2, annotation_clip=False)


def _context_lines(ax, df, code, cfg, max_year=None):
    """Draw comparator countries in gray; return their end-label items."""
    focus = cfg["focus_country"]
    items = []
    for iso3, name in cfg["countries"].items():
        if iso3 == focus:
            continue
        s = series(df, code, iso3, max_year=max_year)
        if s.empty:
            continue
        ax.plot(s.year, s.value, color=CONTEXT, linewidth=1.5, zorder=2)
        items.append((name, s.year.iloc[-1], s.value.iloc[-1], False))
    return items


def _focus_line(ax, df, code, cfg, max_year=None, band=True):
    s = series(df, code, cfg["focus_country"], max_year=max_year)
    if band and s.low.notna().all():
        ax.fill_between(s.year, s.low, s.high, color=FOCUS, alpha=0.12, linewidth=0, zorder=1)
    ax.plot(s.year, s.value, color=FOCUS, linewidth=2.5, zorder=3)
    return [(cfg["countries"][cfg["focus_country"]], s.year.iloc[-1], s.value.iloc[-1], True)]


def _country_panel(ax, df, code, cfg, max_year=None, band=True):
    items = _context_lines(ax, df, code, cfg, max_year) + _focus_line(ax, df, code, cfg, max_year, band)
    _end_labels(ax, items)


def fig_premature_mortality(df, cfg, sdg: dict, path: Path):
    _style()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    code = "NCDMORT3070"
    _country_panel(ax, df, code, cfg)
    ax.plot([sdg["baseline_year"], 2030], [sdg["baseline_value"], sdg["target_value"]],
            color=FOCUS, linestyle=(0, (3, 3)), linewidth=1.5, zorder=3)
    ax.plot([2030], [sdg["target_value"]], marker="o", markersize=8, color=FOCUS,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=4)
    ax.annotate(f"SDG 3.4 target for Libya: {sdg['target_value']:.1f}%", (2030, sdg["target_value"]),
                xytext=(0, -16), textcoords="offset points", ha="center", fontsize=8, color=INK_2)
    ax.set_xlim(2000, 2033)
    ax.set_ylabel("Probability of dying aged 30–70 (%)")
    ax.set_title("Premature NCD mortality in Libya has barely moved since 2000")
    return _finish(fig, path, SOURCE_NOTE + " SDG 3.4.1: deaths from cardiovascular disease, cancer, diabetes or chronic respiratory disease.\n"
                   "Band: Libya 95% uncertainty interval. Dashed: path required to meet SDG 3.4 by 2030.")


def fig_mortality_by_sex(df, cfg, path: Path):
    _style()
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for sex, color, name in [("male", FOCUS, "Men"), ("female", SECOND, "Women")]:
        s = series(df, "NCDMORT3070", cfg["focus_country"], sex=sex)
        ax.fill_between(s.year, s.low, s.high, color=color, alpha=0.10, linewidth=0)
        ax.plot(s.year, s.value, color=color, label=name)
        ax.annotate(name, (s.year.iloc[-1], s.value.iloc[-1]), xytext=(4, 0), textcoords="offset points",
                    fontsize=9, color=INK, va="center")
    ax.set_xlim(2000, 2023.5)
    ax.set_ylabel("Premature NCD mortality (%)")
    ax.set_title("Libya: premature NCD mortality is consistently higher in men")
    ax.legend(loc="upper left", fontsize=8)
    return _finish(fig, path, SOURCE_NOTE + " Bands: 95% uncertainty intervals — they overlap, so the size of the gap is uncertain.")


def fig_risk_factors(df, cfg, path: Path):
    _style()
    codes = [c for c, m in cfg["who_gho"]["indicators"].items() if m["domain"] == "risk_factor"] + ["NCD_HYP_PREVALENCE_A"]
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.4), sharex=True)
    max_year = cfg.get("max_observed_year")
    for ax, code in zip(axes.flat, codes):
        _country_panel(ax, df, code, cfg, max_year=max_year)
        ax.set_title(cfg["who_gho"]["indicators"][code]["short"] + " (%)", fontsize=10)
        ax.set_xlim(2000, 2029)
    axes.flat[-1].axis("off")
    axes.flat[-1].text(0.0, 0.6, "Libya (blue) vs. Tunisia, Algeria,\nEgypt and Morocco (gray).\n\n"
                       "All age-standardized, adults.\nBand = Libya 95% UI.", fontsize=9, color=INK_2,
                       transform=axes.flat[-1].transAxes)
    fig.suptitle("Libya has the region's highest diabetes, hypertension and physical-inactivity levels",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    return _finish(fig, path)


def fig_cascade(cascades: list[dict], cfg, path: Path):
    _style()
    df = pd.DataFrame(cascades).sort_values("controlled")
    names = [cfg["countries"][i] for i in df.iso3]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    left = np.zeros(len(df))
    parts = [("controlled", "Controlled"), ("treated_not_controlled", "Treated, not controlled"),
             ("diagnosed_not_treated", "Diagnosed, not treated"), ("undiagnosed", "Undiagnosed")]
    for key, label in parts:
        ax.barh(names, df[key], left=left, color=CASCADE[key], label=label, height=0.62,
                edgecolor=SURFACE, linewidth=2)
        left += df[key].values
    for i, (_, r) in enumerate(df.iterrows()):
        ax.text(r.controlled - 0.8, i, f"{r.controlled:.0f}%", ha="right", va="center", fontsize=8, color="white")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("% of adults aged 30–79 with hypertension")
    for lbl in ax.get_yticklabels():
        if lbl.get_text() == cfg["countries"][cfg["focus_country"]]:
            lbl.set_fontweight("bold")
            lbl.set_color(INK)
    ax.legend(ncol=4, loc="upper left", bbox_to_anchor=(0, -0.22), fontsize=8)
    year = int(df.year.max())
    ax.set_title(f"Only about 1 in 9 Libyans with hypertension has it controlled ({year})")
    return _finish(fig, path)


def fig_financing(df, cfg, path: Path):
    _style()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, code, title in [(a1, "GHED_CHE_pc_US_SHA2011", "Current health spending per person (US$)"),
                            (a2, "GHED_OOPSCHE_SHA2011", "Out-of-pocket share of health spending (%)")]:
        _country_panel(ax, df, code, cfg, band=False)
        ax.set_title(title, fontsize=10)
        ax.set_xlim(2000, 2026.5)
    for yr, txt in [(2011, "2011"), (2014, "2014")]:
        a1.axvline(yr, color=MUTED, linewidth=0.8, linestyle=":")
        a1.annotate(txt, (yr, a1.get_ylim()[1]), xytext=(2, -10), textcoords="offset points", fontsize=7, color=MUTED)
    fig.suptitle("Libya spends the most per person on health, but the amount swings sharply year to year",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    return _finish(fig, path, SOURCE_NOTE + " Global Health Expenditure Database. Dotted lines: 2011 conflict, 2014 second civil war.")


def fig_tornado(owsa: pd.DataFrame, path: Path, swing: float = 0.25):
    _style()
    d = owsa.iloc[::-1]
    base = float(d.base_icer.iloc[0])
    fig, ax = plt.subplots(figsize=(8, 4.2))
    labels = [PARAM_LABELS.get(p, p) + ("  *" if s == "assumption" else "") for p, s in zip(d.parameter, d.source)]
    lo = d[["icer_low_input", "icer_high_input"]].min(axis=1)
    hi = d[["icer_low_input", "icer_high_input"]].max(axis=1)
    ax.barh(labels, hi - lo, left=lo, color=FOCUS, height=0.55, edgecolor=SURFACE, linewidth=2)
    ax.axvline(base, color=INK, linewidth=1)
    ax.annotate(f"Base case ${base:,.0f}/DALY", (base, -0.6), xytext=(4, 0), textcoords="offset points",
                fontsize=8, color=INK_2, va="center")
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Net cost per DALY averted (US$)")
    ax.set_title(f"What drives the cost per DALY? (each input ±{swing:.0%})")
    return _finish(fig, path, "* Illustrative assumption — see config.yaml. Population size scales costs and DALYs equally, so it does not move the ratio.")


def fig_ceac(curve: pd.DataFrame, gdp_pc: float, multiples: list[float], path: Path):
    _style()
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(curve.wtp_per_daly, 100 * curve.prob_cost_effective, color=FOCUS)
    for m in multiples:
        x = m * gdp_pc
        p = float(np.interp(x, curve.wtp_per_daly, curve.prob_cost_effective))
        ax.axvline(x, color=MUTED, linewidth=0.8, linestyle=":")
        ax.annotate(f"{m:g}× GDP/cap\n{100 * p:.0f}%", (x, 100 * p), xytext=(4, -18), textcoords="offset points",
                    fontsize=8, color=INK_2)
    ax.set_ylim(0, 102)
    ax.set_xlabel("Willingness to pay per DALY averted (US$)")
    ax.set_ylabel("Probability cost-effective (%)")
    ax.set_title("Cost-effectiveness acceptability curve: hypertension-control scale-up")
    return _finish(fig, path, "Probabilistic sensitivity analysis, 5,000 draws. Inputs and their sources: config.yaml and docs/ECONOMIC_MODEL.md.")


# --- GBD level-2 burden figures -------------------------------------------------------
YLL_COLOR, YLD_COLOR = FOCUS, SECOND
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
GBD_NOTE = "Source: GBD 2023 (IHME, 2024), all ages, both sexes."


def fig_leading_causes(lead: pd.DataFrame, year: int, path: Path):
    _style()
    d = lead.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.barh(d.cause, d.ylls / 1e3, color=YLL_COLOR, height=0.62, label="Years of life lost (premature death)",
            edgecolor=SURFACE, linewidth=2)
    ax.barh(d.cause, d.ylds / 1e3, left=d.ylls / 1e3, color=YLD_COLOR, height=0.62,
            label="Years lived with disability", edgecolor=SURFACE, linewidth=2)
    for i, (_, r) in enumerate(d.iterrows()):
        ax.text(r.dalys / 1e3 + 4, i, f"{r.dalys_share_pct:.1f}%", va="center", fontsize=8, color=INK_2)
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("DALYs (thousands)")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_title(f"Leading causes of disease burden in Libya, {year}")
    return _finish(fig, path, GBD_NOTE + f" Labels: share of all DALYs.\n{year} is the baseline: injury DALYs spike in 2023, the year of the Derna flood.")


def fig_burden_heatmap(mat: pd.DataFrame, cfg, year: int, path: Path):
    _style()
    order = [cfg["focus_country"]] + [c for c in cfg["countries"] if c != cfg["focus_country"]]
    mat = mat[order]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    vmax = float(mat.values.max())
    bins = np.linspace(0, vmax, len(SEQ) + 1)
    for i, cause in enumerate(mat.index):
        for j, iso in enumerate(mat.columns):
            v = float(mat.loc[cause, iso])
            k = min(int(np.searchsorted(bins, v, side="right")) - 1, len(SEQ) - 1)
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=SEQ[k], edgecolor=SURFACE, linewidth=2))
            ax.text(j + 0.5, i + 0.5, f"{v:.1f}", ha="center", va="center", fontsize=8,
                    color="white" if k >= 3 else INK)
    ax.set_xlim(0, len(mat.columns))
    ax.set_ylim(len(mat.index), 0)
    ax.set_xticks(np.arange(len(mat.columns)) + 0.5)
    ax.set_xticklabels([cfg["countries"][c] for c in mat.columns], fontsize=9)
    ax.set_yticks(np.arange(len(mat.index)) + 0.5)
    ax.set_yticklabels(mat.index, fontsize=9)
    ax.tick_params(length=0)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.xaxis.tick_top()
    ax.get_xticklabels()[0].set_fontweight("bold")
    ax.set_title(f"Share of all DALYs by cause (%), {year}", pad=24)
    return _finish(fig, path, GBD_NOTE + " Shares, not rates, so differences in age structure matter less.")


def fig_burden_shocks(burden: pd.DataFrame, iso3: str, path: Path):
    _style()
    panels = ["Cardiovascular diseases", "Respiratory infections & TB", "Self-harm & interpersonal violence", "Unintentional injuries"]
    events = {"Self-harm & interpersonal violence": [(2011, "2011 uprising", "right"), (2014, "2014 civil war", "left")],
              "Respiratory infections & TB": [(2021, "COVID-19", "right")],
              "Unintentional injuries": [(2023, "Sept 2023 Derna flood", "right")]}
    fig, axes = plt.subplots(2, 2, figsize=(11, 5.8), sharex=True)
    for ax, cause in zip(axes.flat, panels):
        s = burden[(burden.iso3 == iso3) & (burden.cause == cause)].sort_values("year")
        ax.plot(s.year, s.dalys / 1e3, color=FOCUS)
        ax.set_title(cause + " — DALYs (thousands)", fontsize=10)
        ax.set_ylim(0, float(s.dalys.max()) / 1e3 * 1.12)
        for yr, label, side in events.get(cause, []):
            ax.axvline(yr, color=MUTED, linewidth=0.8, linestyle=":")
            ax.annotate(label, (yr, ax.get_ylim()[1]), xytext=(-4 if side == "right" else 4, -10),
                        textcoords="offset points", ha=side, fontsize=7.5, color=INK_2)
    fig.suptitle("Libya's disease burden: a rising NCD load, with conflict, pandemic and disaster shocks on top",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    return _finish(fig, path, GBD_NOTE + " GBD counts war under self-harm & interpersonal violence, COVID-19 under respiratory infections,\nand natural disasters under unintentional injuries.")
