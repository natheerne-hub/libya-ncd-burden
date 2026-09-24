"""Write outputs/RESULTS.md from the computed results (no hand-typed numbers)."""
from __future__ import annotations

from pathlib import Path


def _pct(x, d=1):
    return f"{x:.{d}f}%"


def write_report(r: dict, cfg: dict, path: Path) -> Path:
    focus = cfg["focus_country"]
    name = cfg["countries"][focus]
    s = r["sdg_3_4"][focus]
    cas = r["cascade"][focus]
    fin = r["financing"][focus]
    e = r["economics"]
    b = e["base_case"]
    n = len(cfg["countries"])

    sdg_rows = "\n".join(
        f"| {cfg['countries'][k]} | {v['baseline_value']:.1f} | {v['latest_value']:.1f} ({v['latest_year']}) | "
        f"{v['target_value']:.1f} | {100 * v['observed_aarc']:+.2f}% | {100 * v['required_aarc']:+.2f}% | "
        f"{'yes' if v['on_track'] else 'no'} |"
        for k, v in r["sdg_3_4"].items())
    rank_rows = "\n".join(
        f"| {ind} | {v['latest_value']:.1f} ({v['latest_year']}) | {v['rank_high_is_1']} of {n} |"
        for ind, v in r["libya_ranks"].items())
    cas_rows = "\n".join(
        f"| {cfg['countries'][k]} | {c['prevalence']:.1f} | {c['diagnosed']:.1f} | {c['treated']:.1f} | {c['controlled']:.1f} |"
        for k, c in r["cascade"].items())
    fin_rows = "\n".join(
        f"| {cfg['countries'][k]} | {f['che_per_capita_usd']:,.0f} | {f['che_pct_gdp']:.1f} | "
        f"{f['gov_share_of_che_pct']:.0f} | {f['oop_share_pct']:.0f} | {f['che_pc_volatility_pct']:.0f} |"
        for k, f in r["financing"].items())
    params = cfg["economics"]["params"]
    assump = [k for k, v in params.items() if v["source"] == "assumption"]
    n_assump, n_params = len(assump), len(params)
    assump_list = ", ".join(f"`{k}`" for k in assump)
    pce = " · ".join(f"{k.replace('_gdp', '')} GDP/cap: {100 * v:.0f}%" for k, v in e["prob_cost_effective"].items())

    g = r.get("gbd_derived")
    if g:
        gbd_text = (
            f"From `data/snapshot/gbd_2023_libya_extract.csv` (GBD 2023 round, year {g['year']}, all ages, both sexes): "
            f"{g['events']:,.0f} incident ischaemic heart disease + stroke events and {g['dalys']:,.0f} DALYs, "
            f"{g['yll_share_pct']:.0f}% of them from premature death (YLL).\n\n"
            f"| Derived input | Value | Assumption behind it |\n|---|---:|---|\n"
            f"| Annual major CVD event rate in hypertensives | {100 * g['event_rate_hypertensive']:.2f}% "
            f"| hypertensives at {g['rr_hypertension']:g}× the risk of normotensives "
            f"({100 * g['event_rate_if_rr_1_5']:.2f}% at 1.5×, {100 * g['event_rate_if_rr_3']:.2f}% at 3×) |\n"
            f"| DALYs per event (discounted) | {g['dalys_per_event_discounted']:.1f} "
            f"| {g['dalys_per_event_undiscounted']:.1f} undiscounted, spread over {g['spread_years']} years |\n\n"
            "Citation: Global Burden of Disease Collaborative Network. GBD 2023 Results. IHME, 2024.")
    else:
        gbd_text = "Not available — see data/README.md."

    bu = r.get("burden")
    if bu:
        rows = "\n".join(f"| {i + 1} | {c['cause']} | {c['dalys']:,.0f} | {c['dalys_share_pct']:.1f}% | {c['yll_share_pct']:.0f}% |"
                          for i, c in enumerate(bu["leading"]))
        cvd = " · ".join(f"{cfg['countries'][k]} {v:.1f}%" for k, v in bu["cvd_share_by_country"].items())
        burden_text = f"""Non-communicable diseases made up **{bu['ncd_share_pct']:.0f}%** of all DALYs in {name} in {bu['base_year']}.
{bu['base_year']} is used as the baseline because injury DALYs spike in 2023, the year of the Derna flood: unintentional-injury DALYs rose from
{bu['injury_dalys_2022']:,.0f} (2022) to {bu['injury_dalys_2023']:,.0f} (2023). Self-harm & interpersonal violence (which includes war)
peaked at {bu['violence_peak_share']:.1f}% of DALYs in {bu['violence_peak_year']}, and respiratory infections (which include COVID-19 in GBD 2023)
at {bu['resp_peak_share']:.1f}% in {bu['resp_peak_year']}; their 2022 share is still above pre-pandemic levels.

| Rank | Cause (GBD level 2) | DALYs | Share | From premature death (YLL) |
|---:|---|---:|---:|---:|
{rows}

Cardiovascular share of DALYs, {bu['base_year']}: {cvd}.

![Leading causes](figures/08_leading_causes_libya.png)
![Share by country](figures/09_daly_share_by_country.png)
![Shocks](figures/10_burden_shocks_libya.png)"""
    else:
        burden_text = "Not available."

    text = f"""# Results — {name}

*Generated automatically by `run_pipeline.py` from `{r['data_source']}`. Do not edit by hand.*

## 1. Premature NCD mortality and SDG 3.4

{name}'s probability of dying between 30 and 70 from the four main NCDs was **{_pct(s['latest_value'])} in {s['latest_year']}**
(baseline {s['baseline_year']}: {_pct(s['baseline_value'])}). Reaching the SDG 3.4 target of {_pct(s['target_value'])} by 2030
requires an average annual change of **{100 * s['required_aarc']:+.2f}%**; the observed trend since {s['baseline_year']} is
{100 * s['observed_aarc']:+.2f}% per year, projecting {_pct(s['projected_target_year_value'])} in 2030 —
**{'on track' if s['on_track'] else 'not on track'}**.

Men–women gap: {r['sex_gap']['first_gap']:.1f} points in {r['sex_gap']['first_year']} → {r['sex_gap']['latest_gap']:.1f} points in {r['sex_gap']['latest_year']}.

| Country | {s['baseline_year']} (%) | Latest (%) | 2030 target (%) | Observed AARC | Required AARC | On track |
|---|---:|---:|---:|---:|---:|:---:|
{sdg_rows}

![Premature NCD mortality](figures/01_premature_ncd_mortality.png)
![By sex](figures/02_libya_mortality_by_sex.png)

## 2. Risk-factor profile — {name}'s rank among {n} countries (1 = highest)

| Indicator | {name} latest | Rank |
|---|---:|:---:|
{rank_rows}

![Risk factors](figures/03_risk_factors.png)

## 3. Hypertension care cascade ({cas['year']}, % of adults 30–79 with hypertension)

In {name}, {_pct(cas['undiagnosed'], 0)} of people with hypertension are undiagnosed and only **{_pct(cas['controlled'])}** are controlled.

| Country | Prevalence | Diagnosed | Treated | Controlled |
|---|---:|---:|---:|---:|
{cas_rows}

![Cascade](figures/04_hypertension_cascade.png)

## 4. Health financing (latest year {fin['latest_year']})

| Country | CHE per capita (US$) | CHE % GDP | Government share of CHE (%) | Out-of-pocket share (%) | Volatility of per-capita spend (SD of YoY %) |
|---|---:|---:|---:|---:|---:|
{fin_rows}

![Financing](figures/05_health_financing.png)

## 5. Health-economic scenario: hypertension control to {100 * e['target_control']:.0f}% in {name}

> ⚠️ **Partly illustrative.** {n_assump} of {n_params} inputs {"is" if n_assump == 1 else "are"} still {"a placeholder" if n_assump == 1 else "placeholders"} (`source: assumption` in `config.yaml`:
> {assump_list}). Two structural assumptions sit inside the GBD derivation (section 6). Treat the results as preliminary.

Inputs from data ({e['input_year']}): prevalence {_pct(100 * e['prevalence'])}, current control {_pct(100 * e['current_control'])}.
Implied GDP per capita (WHO GHED): US${e['gdp_per_capita_usd']:,.0f}.

| Output ({cfg['economics']['horizon_years']}-year horizon, {100 * cfg['economics']['discount_rate']:.0f}% discount) | Base case |
|---|---:|
| Additional people controlled | {b['additional_controlled']:,.0f} |
| Gross programme cost (US$) | {b['gross_cost']:,.0f} |
| Averted CVD treatment costs (US$) | {b['cost_offsets']:,.0f} |
| Net cost (US$) | {b['net_cost']:,.0f} |
| Major CVD events averted | {b['events_averted']:,.0f} |
| DALYs averted (discounted) | {b['dalys_averted']:,.0f} |
| **Net cost per DALY averted** | **US${b['icer_per_daly']:,.0f}** |

PSA ({cfg['economics']['psa_iterations']:,} draws): median ICER US${e['psa_icer_median']:,.0f}
(95% UI {e['psa_icer_95ui'][0]:,.0f} to {e['psa_icer_95ui'][1]:,.0f}). Probability cost-effective — {pce}.
Most influential input: `{e['most_influential_parameter']}`.

![Tornado](figures/06_tornado.png)
![CEAC](figures/07_ceac.png)

## 6. Burden of disease in Libya (GBD 2023)

{burden_text}

## 7. Inputs derived from GBD 2023 (Libya)

{gbd_text}
"""
    path.write_text(text, encoding="utf-8")
    return path
