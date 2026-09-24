"""End-to-end pipeline: data → validation → metrics → economics → figures → report.

    python run_pipeline.py            # uses latest fetch if present, else snapshot
    python run_pipeline.py --fetch    # refresh from the WHO GHO API first
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import economics as econ
from . import metrics as m
from . import plots
from .config import EXTERNAL, FIGURES, OUTPUTS, ROOT, TABLES, load_config
from .data import fetch_who_gho, load_who, series, validate_who


def run(fetch: bool = False) -> dict:
    cfg = load_config()
    focus = cfg["focus_country"]
    if fetch:
        print("Fetching WHO GHO data …")
        fetch_who_gho(cfg)
    df = load_who()
    print(f"Loaded {len(df):,} rows from {df.attrs['source_path']}")

    problems = validate_who(df, cfg)
    if problems:
        raise SystemExit("Data validation failed:\n  - " + "\n  - ".join(problems))
    print("Data validation: passed")

    TABLES.mkdir(parents=True, exist_ok=True)
    results: dict = {"data_source": str(Path(df.attrs["source_path"]).resolve().relative_to(ROOT))}

    # RQ1 — premature NCD mortality and SDG 3.4
    sdg_cfg = cfg["sdg_3_4"]
    sdg = {iso3: m.sdg_34_progress(series(df, "NCDMORT3070", iso3), sdg_cfg["baseline_year"],
                                   sdg_cfg["target_year"], sdg_cfg["relative_reduction"])
           for iso3 in cfg["countries"]}
    pd.DataFrame(sdg).T.to_csv(TABLES / "sdg_3_4_progress.csv")
    results["sdg_3_4"] = sdg

    by_sex = {s: series(df, "NCDMORT3070", focus, sex=s) for s in ("male", "female")}
    results["sex_gap"] = {
        "first_year": int(by_sex["male"].year.iloc[0]),
        "first_gap": float(by_sex["male"].value.iloc[0] - by_sex["female"].value.iloc[0]),
        "latest_year": int(by_sex["male"].year.iloc[-1]),
        "latest_gap": float(by_sex["male"].value.iloc[-1] - by_sex["female"].value.iloc[-1]),
    }

    # RQ2 — risk factors
    codes = [c for c, meta in cfg["who_gho"]["indicators"].items() if meta["domain"] in ("outcome", "risk_factor")]
    comp = m.comparison_table(df, cfg, codes + ["NCD_HYP_PREVALENCE_A"])
    comp.to_csv(TABLES / "indicator_comparison.csv", index=False)
    results["libya_ranks"] = comp[comp.iso3 == focus].set_index("indicator")[["latest_year", "latest_value", "rank_high_is_1"]].to_dict("index")

    # RQ3 — hypertension care cascade
    cascades = [m.hypertension_cascade(df, iso3) for iso3 in cfg["countries"]]
    pd.DataFrame(cascades).to_csv(TABLES / "hypertension_cascade.csv", index=False)
    results["cascade"] = {c["iso3"]: c for c in cascades}

    # RQ4 — health financing
    fin = [m.financing_profile(df, iso3) for iso3 in cfg["countries"]]
    pd.DataFrame(fin).to_csv(TABLES / "financing_profile.csv", index=False)
    results["financing"] = {f["iso3"]: f for f in fin}

    # RQ5 — health-economic scenario (Libya)
    cas = results["cascade"][focus]
    prev_row = df[(df.indicator_code == "NCD_HYP_PREVALENCE_A") & (df.iso3 == focus) & (df.year == cas["year"])].iloc[0]
    ctrl_row = df[(df.indicator_code == "NCD_HYP_CONTROL_A") & (df.iso3 == focus) & (df.year == cas["year"])].iloc[0]
    prevalence, control = prev_row.value / 100, ctrl_row.value / 100

    # Replace the `source: gbd` inputs with values derived from the committed GBD extract
    from . import gbd
    gd = cfg["economics"].get("gbd_derivation")
    if gd and (ROOT / gd["extract"]).exists():
        params = cfg["economics"]["params"]
        derived = gbd.derive_economic_inputs(
            pd.read_csv(ROOT / gd["extract"]), params["population_30_79"]["value"], prevalence,
            gd["rr_hypertension"], cfg["economics"]["discount_rate"], gd["spread_years"])
        sens = {rr: gbd.derive_economic_inputs(pd.read_csv(ROOT / gd["extract"]), params["population_30_79"]["value"],
                                               prevalence, rr, cfg["economics"]["discount_rate"], gd["spread_years"])
                ["event_rate_hypertensive"] for rr in (1.5, 3.0)}
        params["baseline_cvd_event_rate_uncontrolled"]["value"] = derived["event_rate_hypertensive"]
        params["dalys_per_cvd_event"]["value"] = derived["dalys_per_event_discounted"]
        derived["event_rate_if_rr_1_5"], derived["event_rate_if_rr_3"] = sens[1.5], sens[3.0]
        derived["rr_hypertension"], derived["spread_years"] = gd["rr_hypertension"], gd["spread_years"]
        results["gbd_derived"] = derived
        print(f"GBD-derived inputs: event rate {derived['event_rate_hypertensive']:.4f}/yr, "
              f"{derived['dalys_per_event_discounted']:.1f} DALYs per event")
    else:
        raise SystemExit("GBD extract missing — see data/README.md")
    base = econ.run_model(econ.build_inputs(cfg, prevalence, control))
    owsa = econ.one_way_sensitivity(cfg, prevalence, control)
    owsa.to_csv(TABLES / "one_way_sensitivity.csv", index=False)
    psa = econ.probabilistic_sensitivity(
        cfg,
        prevalence=(prevalence, econ.ci_to_sd(prev_row.low, prev_row.high) / 100),
        current_control=(control, econ.ci_to_sd(ctrl_row.low, ctrl_row.high) / 100),
    )
    gdp_cfg = cfg["economics"].get("gdp_per_capita")
    gdp_pc = float(gdp_cfg["value_usd"]) if gdp_cfg else results["financing"][focus]["implied_gdp_per_capita_usd"]
    multiples = cfg["economics"]["wtp_multiples_of_gdp_pc"]
    curve = econ.ceac(psa, np.linspace(0, 3.5 * gdp_pc, 141))
    curve.to_csv(TABLES / "ceac.csv", index=False)
    results["economics"] = {
        "input_year": cas["year"], "prevalence": prevalence, "current_control": control,
        "target_control": cfg["economics"]["target_control_rate"], "base_case": base,
        "gdp_per_capita_usd": gdp_pc,
        "gdp_per_capita_source": (f"{gdp_cfg['source']}, {gdp_cfg['year']}" if gdp_cfg else "implied from WHO GHED"),
        "psa_icer_median": float(psa.icer_per_daly.median()),
        "psa_icer_95ui": [float(psa.icer_per_daly.quantile(0.025)), float(psa.icer_per_daly.quantile(0.975))],
        "prob_cost_effective": {f"{k:g}x_gdp": float(((k * gdp_pc * psa.dalys_averted - psa.net_cost) > 0).mean())
                                for k in multiples},
        "most_influential_parameter": owsa.parameter.iloc[0],
    }

    # Optional GBD module
    gbd_path = EXTERNAL / "gbd_libya.csv"
    if gbd_path.exists():
        from . import gbd
        g = gbd.load_gbd(gbd_path)
        year = int(g.year.max())
        gbd.top_causes(g, year).to_csv(TABLES / "gbd_top_causes.csv", index=False)
        gbd.daly_composition(g, year).to_csv(TABLES / "gbd_daly_composition.csv", index=False)
        results["gbd"] = {"year": year, "status": "included"}
        print(f"GBD module: included ({year})")
    else:
        results["gbd"] = {"status": "full export not present; economic inputs use the committed extract"}

    # GBD level-2 burden: leading causes, cross-country shares, shocks over time
    burden_path = ROOT / "data" / "snapshot" / "gbd_2023_level2_burden.csv"
    if burden_path.exists():
        from . import gbd as _gbd
        burden = _gbd.load_burden(burden_path)
        base_year = 2022  # injury DALYs spike ~9x in 2023, the year of the Derna flood
        lead = _gbd.leading_causes(burden, focus, base_year, n=10)
        lead.to_csv(TABLES / "gbd_leading_causes_libya.csv", index=False)
        top_causes = list(lead.cause.head(8))
        mat = _gbd.share_matrix(burden, base_year, top_causes)
        mat.to_csv(TABLES / "gbd_daly_share_by_country.csv")
        lby = burden[burden.iso3 == focus]
        inj = lby[lby.cause == "Unintentional injuries"].set_index("year").dalys
        vio = lby[lby.cause == "Self-harm & interpersonal violence"].set_index("year")
        results["burden"] = {
            "base_year": base_year,
            "leading": lead[["cause", "dalys", "dalys_share_pct", "yll_share_pct"]].to_dict("records"),
            "ncd_share_pct": float(lby[(lby.year == base_year) & lby.cause_id.isin(
                [410, 491, 508, 526, 542, 558, 626, 640, 653, 669, 973, 974])].dalys_share_pct.sum()),
            "cvd_share_rank_among_countries": int(mat.loc["Cardiovascular diseases"].rank(ascending=False)[focus]),
            "cvd_share_by_country": mat.loc["Cardiovascular diseases"].to_dict(),
            "injury_dalys_2022": float(inj.get(2022)), "injury_dalys_2023": float(inj.get(2023)),
            "violence_peak_year": int(vio.dalys_share_pct.idxmax()), "violence_peak_share": float(vio.dalys_share_pct.max()),
            "resp_peak_year": int(lby[lby.cause_id == 956].set_index("year").dalys_share_pct.idxmax()),
            "resp_peak_share": float(lby[lby.cause_id == 956].dalys_share_pct.max()),
        }
        plots.fig_leading_causes(lead, base_year, FIGURES / "08_leading_causes_libya.png")
        plots.fig_burden_heatmap(mat, cfg, base_year, FIGURES / "09_daly_share_by_country.png")
        plots.fig_burden_shocks(burden, focus, FIGURES / "10_burden_shocks_libya.png")

    # Figures
    plots.fig_premature_mortality(df, cfg, sdg[focus], FIGURES / "01_premature_ncd_mortality.png")
    plots.fig_mortality_by_sex(df, cfg, FIGURES / "02_libya_mortality_by_sex.png")
    plots.fig_risk_factors(df, cfg, FIGURES / "03_risk_factors.png")
    plots.fig_cascade(cascades, cfg, FIGURES / "04_hypertension_cascade.png")
    plots.fig_financing(df, cfg, FIGURES / "05_health_financing.png")
    plots.fig_tornado(owsa, FIGURES / "06_tornado.png")
    plots.fig_ceac(curve, gdp_pc, multiples, FIGURES / "07_ceac.png")
    print(f"Figures written to {FIGURES}")

    with open(OUTPUTS / "results.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, default=float)
    from .report import write_report
    write_report(results, cfg, OUTPUTS / "RESULTS.md")
    print(f"Report written to {OUTPUTS / 'RESULTS.md'}")
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fetch", action="store_true", help="refresh data from the WHO GHO API first")
    run(fetch=ap.parse_args().fetch)


if __name__ == "__main__":
    main()
