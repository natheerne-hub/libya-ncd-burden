# Analysis plan

Written before interpreting results, so the questions drive the analysis rather than the reverse.

## Research questions

| # | Question | Metric | Output |
|---|---|---|---|
| RQ1 | Is Libya on track for SDG 3.4 (one-third reduction in premature NCD mortality, 2015 → 2030)? How does it compare with its neighbours? | Probability of dying 30–70 (SDG 3.4.1); log-linear average annual rate of change (AARC); required vs. observed AARC | `sdg_3_4_progress.csv`, Fig. 1–2 |
| RQ2 | Which modifiable risk factors are most elevated in Libya relative to the region, and how have they moved since 2000? | Age-standardized prevalence; rank among five countries; AARC | `indicator_comparison.csv`, Fig. 3 |
| RQ3 | Where do people with hypertension drop out of care? | Care cascade: diagnosed → treated → controlled, % of all hypertensives | `hypertension_cascade.csv`, Fig. 4 |
| RQ4 | How much does Libya spend on health, who pays, and how stable is it? | CHE per capita and % GDP; government and out-of-pocket shares; SD of year-on-year change | `financing_profile.csv`, Fig. 5 |
| RQ5 | Under explicit assumptions, what would it cost per DALY averted to raise hypertension control to 50%? How uncertain is that? | Net cost, DALYs averted, ICER; one-way SA; PSA; CEAC | `one_way_sensitivity.csv`, `ceac.csv`, Fig. 6–7 |

## Comparators

Tunisia, Algeria, Egypt and Morocco: North African neighbours with shared epidemiological and dietary
patterns and similar health-system history, which makes the comparison informative. Middle-income
Gulf states were left out because their income levels and health-financing models are very different.

## Methods notes

* **AARC**: slope *b* of ln(value) on year across all points in the window, reported as e^b − 1.
  More robust to a single noisy year than a two-point compound rate.
* **SDG 3.4 projection**: latest value extended at the observed 2015→latest AARC. This is a simple
  extrapolation, not a forecast model.
* **Cascade**: WHO publishes diagnosis, treatment and control as percentages of *all* people with
  hypertension, so the losses between stages can be subtracted directly.
* **Implied GDP per capita** = CHE per capita ÷ (CHE % GDP). Using WHO's own pair of series keeps the
  numerator and denominator consistent. It is used only as a reference point for the cost-effectiveness threshold.
* **Uncertainty**: WHO 95% uncertainty intervals are shown for Libya and passed into the PSA
  (hypertension prevalence and control are drawn from beta distributions fitted to them).

## Limitations (to state in any write-up)

1. **Modelled estimates, not raw surveillance.** Most WHO NCD indicators for Libya come from models
   informed by few national surveys (the 2009 STEPS survey is the main one). The wide intervals are real,
   and small year-to-year changes should not be over-interpreted.
2. **Ecological comparison.** Country-level differences do not identify their causes.
3. **Conflict years.** Health data and spending in 2011 and 2014–2020 are affected by conflict,
   duplicated institutions and exchange-rate distortions (the official and parallel rates diverged).
4. **Economic model is preliminary.** See `ECONOMIC_MODEL.md`: 1 of 7 inputs is still a placeholder, and the GBD-derived inputs rest on two stated assumptions.
5. **No sub-national analysis.** Differences between the east, west and south of Libya are likely large but not captured.

## Extensions

* Add GBD cause-level DALYs (data/README.md) → YLL/YLD composition and leading causes.
* Replace every `source: assumption` economic input with a cited Libyan or regional value.
* Decompose the change in NCD deaths into population growth, population ageing and rate change.
* Add an equity lens (sex now; sub-national if Libyan STEPS microdata become available).
