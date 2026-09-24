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
GDP per capita (threshold reference): US$6,569 (World Bank, GDP per capita (current US$), NY.GDP.PCAP.CD (WDI update of 13 Jul 2026), 2024).

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
(95% UI 646 to 5,321). Probability cost-effective — 0.5x GDP/cap: 83% · 1x GDP/cap: 99% · 3x GDP/cap: 100%.
Most influential input: `baseline_cvd_event_rate_uncontrolled`.

![Tornado](figures/06_tornado.png)
![CEAC](figures/07_ceac.png)

## 6. Burden of disease in Libya (GBD 2023)

Non-communicable diseases made up **76%** of all DALYs in Libya in 2022.
2022 is used as the baseline because injury DALYs spike in 2023, the year of the Derna flood: unintentional-injury DALYs rose from
87,802 (2022) to 769,048 (2023). Self-harm & interpersonal violence (which includes war)
peaked at 21.1% of DALYs in 2011, and respiratory infections (which include COVID-19 in GBD 2023)
at 20.8% in 2021; their 2022 share is still above pre-pandemic levels.

| Rank | Cause (GBD level 2) | DALYs | Share | From premature death (YLL) |
|---:|---|---:|---:|---:|
| 1 | Cardiovascular diseases | 436,810 | 20.9% | 91% |
| 2 | Other non-communicable diseases | 199,911 | 9.5% | 54% |
| 3 | Neoplasms | 193,794 | 9.3% | 98% |
| 4 | Mental disorders | 174,296 | 8.3% | 0% |
| 5 | Diabetes & kidney diseases | 151,516 | 7.2% | 49% |
| 6 | Musculoskeletal disorders | 145,658 | 6.9% | 1% |
| 7 | Respiratory infections & TB | 137,573 | 6.6% | 69% |
| 8 | Unintentional injuries | 87,802 | 4.2% | 56% |
| 9 | Neurological disorders | 84,422 | 4.0% | 26% |
| 10 | Transport injuries | 80,382 | 3.8% | 83% |

Cardiovascular share of DALYs, 2022: Algeria 21.4% · Egypt 27.8% · Libya 20.9% · Morocco 30.1% · Tunisia 11.4%.

![Leading causes](figures/08_leading_causes_libya.png)
![Share by country](figures/09_daly_share_by_country.png)
![Shocks](figures/10_burden_shocks_libya.png)

## 7. Inputs derived from GBD 2023 (Libya)

From `data/snapshot/gbd_2023_libya_extract.csv` (GBD 2023 round, year 2023, all ages, both sexes): 25,398 incident ischaemic heart disease + stroke events and 379,212 DALYs, 93% of them from premature death (YLL).

| Derived input | Value | Assumption behind it |
|---|---:|---|
| Annual major CVD event rate in hypertensives | 1.01% | hypertensives at 2× the risk of normotensives (0.89% at 1.5×, 1.17% at 3×) |
| DALYs per event (discounted) | 11.9 | 14.9 undiscounted, spread over 15 years |

Citation: Global Burden of Disease Collaborative Network. GBD 2023 Results. IHME, 2024.
