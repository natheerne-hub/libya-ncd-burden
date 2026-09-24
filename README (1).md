# Data

| Folder | What | In git? |
|---|---|---|
| `snapshot/who_gho_snapshot.csv` | Frozen extract of 13 WHO GHO indicators for Libya, Tunisia, Algeria, Egypt and Morocco, 2000–2024 | ✅ — makes the analysis reproducible offline and in CI |
| `raw/who_gho_latest.csv` | Fresh pull written by `python run_pipeline.py --fetch` (used in preference to the snapshot when present) | ❌ |
| `external/gbd_libya.csv` | Your own IHME GBD export (optional module) | ❌ — GBD terms do not allow redistribution |

## WHO Global Health Observatory snapshot

* **Source:** WHO GHO OData API, `https://ghoapi.azureedge.net/api/<INDICATOR>`
* **Extracted:** 24 September 2026
* **Schema:** `indicator_code, iso3, year, sex, value, low, high` (`low`/`high` = 95% uncertainty interval where WHO publishes one)
* **Scope of the snapshot:** sex = `both` for every country; Libya additionally has male/female for `NCDMORT3070`.
  Uncertainty intervals are kept for Libya only. Run `--fetch` to get the full set for every country and sex.
* **Age bands:** where GHO splits an indicator by age (`Dim2`), only the overall band is kept
  (`AGEGROUP_YEARS30-69` for premature mortality, `AGEGROUP_YEARS18-PLUS` for diabetes, obesity, inactivity).
* **Projections:** WHO tobacco estimates run to 2030; values after `max_observed_year` (config) are excluded from analysis.

| Code | Indicator | Domain |
|---|---|---|
| `NCDMORT3070` | Probability of dying 30–70 from CVD, cancer, diabetes or chronic respiratory disease (SDG 3.4.1) | Outcome |
| `NCD_DIABETES_PREVALENCE_AGESTD` | Diabetes prevalence, age-standardized | Risk factor |
| `NCD_BMI_30A` | Obesity (BMI ≥ 30), age-standardized | Risk factor |
| `NCD_PAA` | Insufficient physical activity, age-standardized | Risk factor |
| `M_Est_tob_curr_std` | Current tobacco use, age-standardized | Risk factor |
| `NCD_HYP_PREVALENCE_A` | Hypertension prevalence 30–79, age-standardized | Cascade |
| `NCD_HYP_DIAGNOSIS_A` / `_TREATMENT_A` / `_CONTROL_A` | Diagnosed / treated / controlled, % of hypertensives | Cascade |
| `GHED_CHEGDP_SHA2011` | Current health expenditure, % of GDP | Financing |
| `GHED_CHE_pc_US_SHA2011` | Current health expenditure per capita, US$ | Financing |
| `GHED_GGHE-D_pc_US_SHA2011` | Domestic government health expenditure per capita, US$ | Financing |
| `GHED_OOPSCHE_SHA2011` | Out-of-pocket spending, % of current health expenditure | Financing |

**Integrity check:** the snapshot was verified against the live API by comparing per-indicator, per-country
value sums (all 65 groups matched exactly). `validate_who()` re-checks ranges, duplicates and interval
consistency on every run.

## Adding GBD (optional, recommended)

1. Go to the IHME **GBD Results** tool (vizhub.healthdata.org/gbd-results) and sign in (free).
2. Select — *Location:* Libya · *Measure:* DALYs, YLLs, YLDs, Deaths · *Metric:* Rate and Number ·
   *Cause:* level-2 and level-3 causes · *Age:* Age-standardized and All ages · *Sex:* Both, Male, Female ·
   *Year:* every year available in the latest round.
3. Download as CSV with the default column layout and save it as `data/external/gbd_libya.csv`.
4. Re-run `python run_pipeline.py` — the GBD module switches on automatically and writes
   `outputs/tables/gbd_top_causes.csv` and `gbd_daly_composition.csv`.
5. Cite GBD as IHME requires and do **not** commit the file.
