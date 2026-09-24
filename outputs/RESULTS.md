# Results — Libya

*Generated automatically by `run_pipeline.py` from `data/snapshot/who_gho_snapshot.csv`. Do not edit by hand.*

## 1. Premature NCD mortality and SDG 3.4

Libya's probability of dying between 30 and 70 from the four main NCDs was **19.8% in 2021**
(baseline 2015: 20.4%). Reaching the SDG 3.4 target of 13.6% by 2030
requires an average annual change of **-4.09%**; the observed trend since 2015 is
-0.46% per year, projecting 19.0% in 2030 —
**not on track**.

Men–women gap: 2.0 points in 2000 → 3.2 points in 2021.

| Country | 2015 (%) | Latest (%) | 2030 target (%) | Observed AARC | Required AARC | On track |
|---|---:|---:|---:|---:|---:|:---:|
| Libya | 20.4 | 19.8 (2021) | 13.6 | -0.46% | -4.09% | no |
| Tunisia | 15.5 | 13.0 (2021) | 10.3 | -2.05% | -2.52% | no |
| Algeria | 14.2 | 13.3 (2021) | 9.5 | -1.46% | -3.71% | no |
| Egypt | 30.1 | 26.0 (2021) | 20.1 | -2.31% | -2.84% | no |
| Morocco | 22.7 | 22.0 (2021) | 15.1 | -0.34% | -4.07% | no |

![Premature NCD mortality](figures/01_premature_ncd_mortality.png)
![By sex](figures/02_libya_mortality_by_sex.png)

## 2. Risk-factor profile — Libya's rank among 5 countries (1 = highest)

| Indicator | Libya latest | Rank |
|---|---:|:---:|
| Premature NCD mortality | 19.8 (2021) | 3 of 5 |
| Diabetes | 28.0 (2022) | 1 of 5 |
| Obesity | 33.7 (2024) | 2 of 5 |
| Physical inactivity | 45.6 (2022) | 1 of 5 |
| Tobacco use | 24.2 (2024) | 3 of 5 |
| Hypertension | 42.7 (2019) | 1 of 5 |

![Risk factors](figures/03_risk_factors.png)

## 3. Hypertension care cascade (2019, % of adults 30–79 with hypertension)

In Libya, 52% of people with hypertension are undiagnosed and only **11.1%** are controlled.

| Country | Prevalence | Diagnosed | Treated | Controlled |
|---|---:|---:|---:|---:|
| Libya | 42.7 | 47.6 | 35.2 | 11.1 |
| Tunisia | 34.7 | 45.4 | 36.7 | 14.6 |
| Algeria | 36.2 | 50.3 | 39.3 | 15.9 |
| Egypt | 38.2 | 53.4 | 44.2 | 18.9 |
| Morocco | 35.3 | 43.0 | 28.8 | 10.1 |

![Cascade](figures/04_hypertension_cascade.png)

## 4. Health financing (latest year 2023)

| Country | CHE per capita (US$) | CHE % GDP | Government share of CHE (%) | Out-of-pocket share (%) | Volatility of per-capita spend (SD of YoY %) |
|---|---:|---:|---:|---:|---:|
| Libya | 470 | 7.8 | 80 | 19 | 28 |
| Tunisia | 318 | 8.0 | 54 | 38 | 9 |
| Algeria | 233 | 4.4 | 53 | 45 | 15 |
| Egypt | 141 | 4.9 | 32 | 57 | 14 |
| Morocco | 232 | 6.1 | 57 | 37 | 8 |

![Financing](figures/05_health_financing.png)

## 5. Health-economic scenario: hypertension control to 50% in Libya

> ⚠️ **Partly illustrative.** 1 of 7 inputs is still a placeholder (`source: assumption` in `config.yaml`:
> `programme_cost_per_additional_patient`). Two structural assumptions sit inside the GBD derivation (section 6). Treat the results as preliminary.

Inputs from data (2019): prevalence 42.7%, current control 11.1%.
Implied GDP per capita (WHO GHED): US$6,027.

| Output (5-year horizon, 3% discount) | Base case |
|---|---:|
| Additional people controlled | 585,925 |
| Gross programme cost (US$) | 144,901,709 |
| Averted CVD treatment costs (US$) | 19,496,593 |
| Net cost (US$) | 125,405,116 |
| Major CVD events averted | 5,913 |
| DALYs averted (discounted) | 64,353 |
| **Net cost per DALY averted** | **US$1,949** |

PSA (5,000 draws): median ICER US$1,993
(95% UI 646 to 5,321). Probability cost-effective — 0.5x GDP/cap: 79% · 1x GDP/cap: 99% · 3x GDP/cap: 100%.
Most influential input: `baseline_cvd_event_rate_uncontrolled`.

![Tornado](figures/06_tornado.png)
![CEAC](figures/07_ceac.png)

## 6. Inputs derived from GBD 2023 (Libya)

From `data/snapshot/gbd_2023_libya_extract.csv` (GBD 2023 round, year 2023, all ages, both sexes): 25,398 incident ischaemic heart disease + stroke events and 379,212 DALYs, 93% of them from premature death (YLL).

| Derived input | Value | Assumption behind it |
|---|---:|---|
| Annual major CVD event rate in hypertensives | 1.01% | hypertensives at 2× the risk of normotensives (0.89% at 1.5×, 1.17% at 3×) |
| DALYs per event (discounted) | 11.9 | 14.9 undiscounted, spread over 15 years |

Citation: Global Burden of Disease Collaborative Network. GBD 2023 Results. IHME, 2024.
