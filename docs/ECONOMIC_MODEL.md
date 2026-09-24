# Economic model: scaling up hypertension control in Libya

> **Status: mostly sourced.** The model structure, code and uncertainty analysis are complete and tested.
> 6 of 7 inputs come from data, GBD 2023 or published literature. One (programme overhead) is still an
> assumption, and the GBD derivation rests on two stated assumptions (relative risk of hypertensives, and the
> years over which an event's DALYs accrue). Results are preliminary until those are checked.

## Decision problem

| | |
|---|---|
| Population | Adults aged 30–79 in Libya with hypertension |
| Intervention | Scale-up of detection and treatment until 50% of hypertensives are controlled (a scenario choice in `config.yaml`) |
| Comparator | Current control rate (WHO estimate) |
| Perspective | Health system (programme costs, and acute CVD treatment costs avoided) |
| Horizon | 5 years, discounted at 3% per year |
| Outcomes | Major CVD events averted; DALYs averted; net cost per DALY averted (ICER) |

## Structure

A transparent cohort calculation (see `src/libya_ncd/economics.py`):

```
hypertensives          N  = population_30_79 × prevalence                    [prevalence: WHO]
additional controlled  ΔC = N × (target − current control)                    [current control: WHO]
annual cost               = ΔC × (treatment cost + programme cost)
events averted / year     = ΔC × event rate if uncontrolled × relative risk reduction
cost offsets / year       = events averted × cost per event
DALYs averted / year      = events averted × DALYs per event
ICER                      = (Σ discounted cost − Σ discounted offsets) / Σ discounted DALYs
```

This is deliberately simpler than a Markov model. It makes each assumption visible and easy to challenge,
and it is the right first step before building a state-transition model.

## Parameters

| Parameter | Base | Status | Source / what would replace it |
|---|---:|---|---|
| Hypertension prevalence 30–79 | 42.7% | data | WHO GHO `NCD_HYP_PREVALENCE_A`, 2019 |
| Current control rate | 11.1% | data | WHO GHO `NCD_HYP_CONTROL_A`, 2019 |
| Population 30–79 | 3.53 M | data | UN World Population Prospects 2024, sum of 5-year groups 30–34 … 75–79 |
| Treatment cost / patient-year | US$44 | literature | Upper end of US$18–44 per person treated per year for the WHO HEARTS package in LMICs: Moran AE, et al. *Rev Panam Salud Publica* 2022;46:e140. Upper end chosen because Libya is upper-middle-income; a Libyan medicine-price survey would be better |
| Programme overhead / new patient-year | US$10 | **assumption** | Libyan programme budget, or the WHO HEARTS costing tool |
| Annual major CVD event rate if uncontrolled | 1.01% | GBD 2023 (derived) | 25,398 incident IHD + stroke events in Libya in 2023 (GBD 2023), split between hypertensive and normotensive adults 30–79 assuming hypertensives carry 2× the risk (0.89% at 1.5×, 1.17% at 3×) |
| Relative risk reduction if controlled | 20% | literature | RR 0.80 (95% CI 0.77–0.83) for major CVD events per 10 mmHg SBP reduction: Ettehad D, et al. *Lancet* 2016;387:957–67. Conservative, because moving from uncontrolled to controlled often lowers SBP by more than 10 mmHg |
| Cost per major CVD event | US$3,600 | literature (regional proxy) | Morocco, mean first-year direct cost per patient: US$3,674 for ischaemic stroke (Fez, *Cureus* 2023) and US$3,520 for ischaemic heart disease (*Value Health Reg Issues* 2026;52). Libyan hospital costing preferred; Libya's higher health spending suggests this is conservative |
| DALYs per CVD event | 11.9 | GBD 2023 (derived) | 379,212 IHD + stroke DALYs ÷ 25,398 events = 14.9 per event (undiscounted, steady-state approximation), discounted at 3% assuming the burden accrues over 15 years |

`population_30_79` changes the size of the programme but not the ratio: the ICER is independent of it, and a unit test enforces this.

### How the GBD inputs are derived

`gbd.derive_economic_inputs()` uses the committed extract `data/snapshot/gbd_2023_libya_extract.csv`:

```
events            = incident IHD + incident stroke (Libya, 2023, all ages)
events / N₃₀₋₇₉   = r₀ · (1 + p · (RR − 1))        p = hypertension prevalence, RR = 2 (assumption)
rate in hypertensives r₁ = RR · r₀
DALYs per event   = (IHD + stroke DALYs) / events, discounted over 15 years
```

Two simplifications to state in any write-up. Events at ages 80+ are included in the numerator but not in
the denominator, which slightly overstates the rate. DALYs ÷ incidence is a cross-sectional approximation
of the lifetime burden per event.

## Uncertainty

* **One-way sensitivity**: each input ±25% → tornado diagram (`06_tornado.png`).
* **Probabilistic (PSA)**: 5,000 draws, fixed seed. Costs and DALYs use gamma distributions, probabilities
  use beta distributions, and population uses a normal distribution. Prevalence and control are drawn from
  the **WHO uncertainty intervals**, so data uncertainty flows into the economic result.
* **CEAC** (`07_ceac.png`): the probability that the scale-up is cost-effective across willingness-to-pay values.

## On thresholds

The chart marks 0.5×, 1× and 3× GDP per capita per DALY only as reference points. The 1–3× GDP rule has
been widely criticised as too permissive, and WHO-CHOICE no longer recommends it. Evidence-based estimates
of country thresholds based on health opportunity cost are usually well below 1× GDP per capita
(e.g. Woods B, et al. *Value Health* 2016). Presenting the full CEAC instead of a yes/no verdict follows from this.

## What would make this publishable

1. Every `assumption` replaced and cited (this table becomes a sourced parameter table).
2. A Markov model (well → controlled / uncontrolled → post-MI / post-stroke → dead) over a lifetime horizon.
3. Costs from a Libyan payer perspective, with sensitivity analysis on the exchange rate.
4. Reporting that follows the CHEERS 2022 checklist.
