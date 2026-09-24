# Economic model: scaling up hypertension control in Libya

> **Status: illustrative.** The model structure, code and uncertainty analysis are complete and tested.
> Several inputs are marked `source: assumption` in `config.yaml`. They are round numbers chosen to be
> plausible, not measured, and the results should not be quoted as estimates for Libya until those inputs
> have been replaced with sourced values.

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

| Parameter | Base | Source status | What to replace it with |
|---|---:|---|---|
| Hypertension prevalence 30–79 | WHO | data | — |
| Current control rate | WHO | data | — |
| Population 30–79 | 3.0 M | assumption | UN World Population Prospects, Libya |
| Treatment cost / patient-year | US$60 | assumption | Libyan public-sector drug prices plus visit costs; WHO HEARTS costing tool |
| Programme cost / new patient-year | US$25 | assumption | Programme budgets from comparable scale-ups in the region |
| Annual major CVD event rate if uncontrolled | 2.0% | assumption | Regional cohort data or a validated risk score applied to STEPS data |
| Relative risk reduction if controlled | 20% | literature | Ettehad D, et al. *Lancet* 2016;387:957–67: about 20% fewer major CVD events per 10 mmHg SBP reduction. Verify that it applies to the achieved BP difference |
| Cost per major CVD event | US$2,500 | assumption | Libyan hospital costing for MI and stroke admissions |
| DALYs per CVD event | 3.0 | assumption | Derive from GBD Libya (DALYs ÷ incident events for IHD + stroke) |

`population_30_79` changes the size of the programme but not the ratio: the ICER is independent of it, and a unit test enforces this.

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
