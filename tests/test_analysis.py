"""Tests for data validation, metrics, economics and the GBD loader.

Written with unittest so they run under both `pytest` and `python -m unittest`.
The GBD fixture in tests/fixtures is SYNTHETIC — shaped like a GBD export but
with made-up numbers; it is only used to test the code path.
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from libya_ncd import economics as econ  # noqa: E402
from libya_ncd import gbd  # noqa: E402
from libya_ncd import metrics as m  # noqa: E402
from libya_ncd.config import SNAPSHOT, load_config  # noqa: E402
from libya_ncd.data import load_who, series, tidy_gho_records, validate_who  # noqa: E402

CFG = load_config()
DF = load_who(SNAPSHOT)


class TestData(unittest.TestCase):
    def test_snapshot_is_clean(self):
        self.assertEqual(validate_who(DF, CFG), [])

    def test_every_indicator_present_for_every_country(self):
        for code in CFG["who_gho"]["indicators"]:
            for iso3 in CFG["countries"]:
                self.assertFalse(series(DF, code, iso3).empty, f"{code}/{iso3} missing")

    def test_validator_catches_problems(self):
        bad = DF.copy()
        bad.loc[bad.index[0], "value"] = 150            # impossible percentage
        bad = pd.concat([bad, bad.iloc[[1]]])            # duplicate row
        problems = validate_who(bad, CFG)
        self.assertTrue(any("outside 0–100" in p for p in problems))
        self.assertTrue(any("duplicate" in p for p in problems))

    def test_tidy_keeps_only_overall_age_band(self):
        recs = [
            {"SpatialDim": "LBY", "TimeDim": 2020, "Dim1": "SEX_BTSX", "Dim2": "AGEGROUP_YEARS18-PLUS", "NumericValue": 30.0},
            {"SpatialDim": "LBY", "TimeDim": 2020, "Dim1": "SEX_BTSX", "Dim2": "AGEGROUP_YEARS60-69", "NumericValue": 55.0},
            {"SpatialDim": "LBY", "TimeDim": 2021, "Dim1": "SEX_BTSX", "Dim2": "AGEGROUP_YEARS18-PLUS", "NumericValue": None},
        ]
        out = tidy_gho_records(recs, "NCD_PAA", "AGEGROUP_YEARS18-PLUS")
        self.assertEqual(len(out), 1)
        self.assertEqual(out.value.iloc[0], 30.0)
        self.assertEqual(out.sex.iloc[0], "both")


class TestMetrics(unittest.TestCase):
    def test_aarc_recovers_known_rate(self):
        years = np.arange(2000, 2011)
        values = 100 * 0.97 ** (years - 2000)
        self.assertAlmostEqual(m.aarc(years, values), -0.03, places=6)

    def test_sdg_target_is_one_third_below_baseline(self):
        s = series(DF, "NCDMORT3070", "LBY")
        r = m.sdg_34_progress(s)
        self.assertAlmostEqual(r["target_value"], r["baseline_value"] * 2 / 3, places=2)
        # required pace must be steeper (more negative) than the observed one if not on track
        if not r["on_track"]:
            self.assertLess(r["required_aarc"], r["observed_aarc"])

    def test_cascade_is_internally_consistent(self):
        for iso3 in CFG["countries"]:
            c = m.hypertension_cascade(DF, iso3)
            self.assertGreaterEqual(c["diagnosed"], c["treated"])
            self.assertGreaterEqual(c["treated"], c["controlled"])
            total = c["controlled"] + c["treated_not_controlled"] + c["diagnosed_not_treated"] + c["undiagnosed"]
            self.assertAlmostEqual(total, 100, places=6)

    def test_implied_gdp_per_capita_is_plausible(self):
        f = m.financing_profile(DF, "LBY")
        self.assertTrue(1_000 < f["implied_gdp_per_capita_usd"] < 50_000)
        self.assertTrue(0 < f["gov_share_of_che_pct"] <= 100)


class TestEconomics(unittest.TestCase):
    def setUp(self):
        self.x = econ.build_inputs(CFG, prevalence=0.40, current_control=0.10)

    def test_annuity_factor(self):
        self.assertAlmostEqual(econ.annuity_factor(0.0, 5), 5.0)
        self.assertAlmostEqual(econ.annuity_factor(0.03, 1), 1 / 1.03)

    def test_hand_calculation(self):
        r = econ.run_model(self.x)
        p = CFG["economics"]["params"]
        additional = p["population_30_79"]["value"] * 0.40 * (CFG["economics"]["target_control_rate"] - 0.10)
        self.assertAlmostEqual(r["additional_controlled"], additional, places=3)
        events = additional * p["baseline_cvd_event_rate_uncontrolled"]["value"] * p["relative_risk_reduction_if_controlled"]["value"]
        net_annual = additional * (p["annual_cost_per_controlled_patient"]["value"] + p["programme_cost_per_additional_patient"]["value"]) \
            - events * p["cost_per_cvd_event"]["value"]
        icer = net_annual / (events * p["dalys_per_cvd_event"]["value"])
        self.assertAlmostEqual(r["icer_per_daly"], icer, places=6)

    def test_icer_is_independent_of_population(self):
        big = econ.run_model(econ.build_inputs(CFG, 0.4, 0.1, {"population_30_79": 9e6}))
        self.assertAlmostEqual(big["icer_per_daly"], econ.run_model(self.x)["icer_per_daly"], places=6)

    def test_no_gain_when_already_at_target(self):
        r = econ.run_model(econ.build_inputs(CFG, 0.4, 0.6))
        self.assertEqual(r["additional_controlled"], 0)
        self.assertTrue(np.isnan(r["icer_per_daly"]))

    def test_psa_is_reproducible_and_ceac_monotone(self):
        a = econ.probabilistic_sensitivity(CFG, (0.43, 0.04), (0.11, 0.04))
        b = econ.probabilistic_sensitivity(CFG, (0.43, 0.04), (0.11, 0.04))
        pd.testing.assert_frame_equal(a, b)
        curve = econ.ceac(a, np.linspace(0, 30000, 50))
        self.assertTrue((np.diff(curve.prob_cost_effective) >= 0).all())
        self.assertEqual(curve.prob_cost_effective.iloc[0], 0.0)

    def test_beta_rejects_impossible_moments(self):
        with self.assertRaises(ValueError):
            econ.beta_draw(np.random.default_rng(0), 0.5, 0.6, 10)


class TestGBD(unittest.TestCase):
    FIX = ROOT / "tests" / "fixtures" / "gbd_synthetic.csv"

    def test_loads_and_ranks(self):
        g = gbd.load_gbd(self.FIX)
        top = gbd.top_causes(g, 2021, n=2)
        self.assertEqual(list(top.cause_name), ["Ischemic heart disease", "Stroke"])

    def test_daly_composition_adds_up(self):
        comp = gbd.daly_composition(gbd.load_gbd(self.FIX), 2021)
        self.assertTrue(((comp.yll_share_pct >= 0) & (comp.yll_share_pct <= 100)).all())
        lbp = comp.set_index("cause_name").loc["Low back pain"]
        self.assertEqual(lbp.yll_share_pct, 0)

    def test_missing_columns_rejected(self):
        self.assertTrue(gbd.validate_gbd(pd.DataFrame({"val": [1]})))


if __name__ == "__main__":
    unittest.main()
