"""Run: uv run python -m unittest scripts.test_salary_compare -v"""
import copy
import json
import unittest

from scripts import salary_compare as sc

DATA = json.loads(sc.TAX_DATA.read_text())
CFG = json.loads(sc.EXAMPLE_CONFIG.read_text())
PKG = CFG["current"]


class TaxTests(unittest.TestCase):
    def test_federal_single_known_value(self):
        # 100k wages -> 83.9k taxable: 1240 + 4560 + 0.22*(83900-50400)
        self.assertAlmostEqual(sc.federal_tax(100000, "single", DATA), 1240 + 4560 + 7370, places=2)

    def test_fica_caps_social_security(self):
        self.assertAlmostEqual(sc.fica_tax(300000, "single", DATA), 184500 * 0.062 + 300000 * 0.0145 + 100000 * 0.009, places=2)

    def test_no_tax_state_and_flat_state(self):
        self.assertEqual(sc.state_tax(100000, {"state": "TX"}, "single", DATA), 0)
        self.assertAlmostEqual(sc.state_tax(100000, {"state": "MI"}, "single", DATA), 4250)

    def test_state_override(self):
        self.assertAlmostEqual(sc.state_tax(100000, {"state": "ZZ", "state_tax_rate_pct": 3}, "single", DATA), 3000)


class PackageTests(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(sc.compute(PKG, "single", DATA), sc.compute(PKG, "single", DATA))

    def test_match_capped(self):
        r = sc.compute(PKG, "single", DATA)  # 6% contrib, 4% cap, base only
        self.assertAlmostEqual(r["employer_401k_match"], 100000 * 0.04)

    def test_taxable_perk_raises_tax_not_net_value_sign(self):
        a = copy.deepcopy(PKG)
        b = copy.deepcopy(PKG)
        for p in b["perks"]:
            p["taxable"] = True
        self.assertGreater(sc.compute(b, "single", DATA)["total_tax"], sc.compute(a, "single", DATA)["total_tax"])

    def test_more_base_more_net(self):
        hi = copy.deepcopy(PKG)
        hi["base_salary"] += 10000
        self.assertGreater(sc.compute(hi, "single", DATA)["net_cash"], sc.compute(PKG, "single", DATA)["net_cash"])


class ReportTests(unittest.TestCase):
    def test_break_even_gives_parity_and_identical_job_is_zero_delta(self):
        offer = {"offer": copy.deepcopy(PKG), "market": {}, "one_time_costs": []}
        rep = sc.build_report(CFG, offer, "single", DATA, None)
        self.assertAlmostEqual(rep["adjusted"]["delta"], 0, places=6)
        self.assertAlmostEqual(rep["break_even_base"], PKG["base_salary"], delta=1)

    def test_cheaper_city_lowers_break_even(self):
        o = copy.deepcopy(PKG)
        o["location"]["cost_of_living_index"] = 80
        rep = sc.build_report(CFG, {"offer": o}, "single", DATA, None)
        self.assertLess(rep["break_even_base"], PKG["base_salary"])


if __name__ == "__main__":
    unittest.main()
