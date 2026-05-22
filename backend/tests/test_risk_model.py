"""
test_risk_model.py
==================
Unit tests untuk MaternalAgeRiskModel dan RiskProfile.

Memverifikasi bahwa nilai risiko konsisten dengan tabel empiris Hook 1981
dan bahwa interpolasi, klasifikasi, serta perbandingan usia berjalan benar.

Sumber validasi:
  Hook EB (1981). https://pubmed.ncbi.nlm.nih.gov/6455611/
  Morris JK et al. (2002). https://pubmed.ncbi.nlm.nih.gov/11943789/
  ACMG (2016). https://pubmed.ncbi.nlm.nih.gov/27467454/
"""

import pytest
from backend.src.models.risk_model import (
    MaternalAgeRiskModel,
    MATERNAL_AGE_RISK_TABLE,
    MEIOSIS_I_FRACTION,
    MEIOSIS_II_FRACTION,
)


class TestMaternalAgeRiskTable:
    """Validasi tabel empiris Hook 1981."""

    def test_table_covers_age_15_to_50(self):
        """Tabel harus mencakup usia 15–50 tahun (36 titik data)."""
        assert min(MATERNAL_AGE_RISK_TABLE.keys()) == 15
        assert max(MATERNAL_AGE_RISK_TABLE.keys()) == 50
        assert len(MATERNAL_AGE_RISK_TABLE) == 36

    def test_table_values_monotonically_increasing(self):
        """
        Risiko harus meningkat seiring usia (atau setidaknya tidak turun).
        Sesuai Hook 1981: korelasi positif usia-risiko.
        """
        ages = sorted(MATERNAL_AGE_RISK_TABLE.keys())
        for i in range(len(ages) - 1):
            assert MATERNAL_AGE_RISK_TABLE[ages[i]] <= MATERNAL_AGE_RISK_TABLE[ages[i + 1]], (
                f"Risiko usia {ages[i]} harus <= usia {ages[i+1]}"
            )

    def test_hook_1981_key_values(self):
        """
        Validasi nilai kunci dari Hook 1981 Tabel 1.
        https://pubmed.ncbi.nlm.nih.gov/6455611/
        """
        table = MATERNAL_AGE_RISK_TABLE
        # Nilai referensi dari Hook (1981)
        assert abs(table[25] - 0.0020) < 0.0001   # ~1/500
        assert abs(table[35] - 0.0105) < 0.0001   # ~1/95 (AMA threshold)
        assert abs(table[40] - 0.0395) < 0.0001   # ~1/25
        assert abs(table[45] - 0.1600) < 0.0001   # ~1/6

    def test_meiosis_fractions_sum_to_one(self):
        """Fraksi Meiosis I dan II harus berjumlah 1.0 (Hassold & Hunt 2001)."""
        assert abs(MEIOSIS_I_FRACTION + MEIOSIS_II_FRACTION - 1.0) < 1e-9

    def test_meiosis_i_dominates(self):
        """
        Meiosis I harus mendominasi (75-80%) sesuai Hassold & Hunt (2001).
        https://pubmed.ncbi.nlm.nih.gov/11283700/
        """
        assert 0.74 <= MEIOSIS_I_FRACTION <= 0.80


class TestInterpolateRisk:
    """Unit tests untuk interpolasi linear."""

    def test_integer_age_returns_exact_table_value(self, risk_model):
        """Usia integer harus mengembalikan nilai tabel persis."""
        for age in [25, 30, 35, 38, 40, 45]:
            assert abs(risk_model.interpolateRisk(age) - MATERNAL_AGE_RISK_TABLE[age]) < 1e-9

    def test_decimal_age_interpolated_between_bounds(self, risk_model):
        """Usia 30.5 harus berada antara risiko usia 30 dan 31."""
        r30  = MATERNAL_AGE_RISK_TABLE[30]
        r31  = MATERNAL_AGE_RISK_TABLE[31]
        r305 = risk_model.interpolateRisk(30.5)
        assert r30 < r305 < r31

    def test_age_below_minimum_clamped(self, risk_model):
        """Usia di bawah 15 harus di-clamp ke nilai usia 15."""
        assert risk_model.interpolateRisk(10) == MATERNAL_AGE_RISK_TABLE[15]

    def test_age_above_maximum_clamped(self, risk_model):
        """Usia di atas 50 harus di-clamp ke nilai usia 50."""
        assert risk_model.interpolateRisk(55) == MATERNAL_AGE_RISK_TABLE[50]


class TestClassifyRisk:
    """Unit tests untuk klasifikasi risiko klinis (ACMG 2016)."""

    def test_rendah_below_half_percent(self, risk_model):
        assert risk_model.classifyRisk(0.001) == "rendah"
        assert risk_model.classifyRisk(0.004) == "rendah"

    def test_sedang_between_half_and_two_percent(self, risk_model):
        assert risk_model.classifyRisk(0.005) == "sedang"
        assert risk_model.classifyRisk(0.015) == "sedang"

    def test_tinggi_between_two_and_eight_percent(self, risk_model):
        assert risk_model.classifyRisk(0.02) == "tinggi"
        assert risk_model.classifyRisk(0.05) == "tinggi"

    def test_sangat_tinggi_above_eight_percent(self, risk_model):
        assert risk_model.classifyRisk(0.08) == "sangat tinggi"
        assert risk_model.classifyRisk(0.20) == "sangat tinggi"


class TestGetRiskProfile:
    """Unit tests untuk objek RiskProfile yang dihasilkan."""

    def test_profile_age25_rendah(self, risk_model):
        profile = risk_model.getRiskProfile(25)
        assert profile.maternalAge == 25
        assert profile.riskCategory == "rendah"
        assert abs(profile.riskRatioToBase - 1.0) < 0.01  # usia 25 = baseline

    def test_profile_age35_sedang(self, risk_model):
        profile = risk_model.getRiskProfile(35)
        assert profile.riskCategory == "sedang"
        assert profile.riskRatioToBase > 5.0  # >5x dibanding usia 25

    def test_profile_age40_tinggi(self, risk_model):
        profile = risk_model.getRiskProfile(40)
        assert profile.riskCategory == "tinggi"

    def test_profile_age45_sangat_tinggi(self, risk_model):
        profile = risk_model.getRiskProfile(45)
        assert profile.riskCategory == "sangat tinggi"

    def test_meiosis_risks_sum_to_total(self, risk_model):
        """meiosisIRisk + meiosisIIRisk harus = totalRisk."""
        for age in [25, 30, 35, 40, 45]:
            p = risk_model.getRiskProfile(age)
            assert abs(p.meiosisIRisk + p.meiosisIIRisk - p.totalRisk) < 1e-9

    def test_to_dict_all_camel_case_keys(self, risk_model):
        """Semua key toDict() harus camelCase."""
        d = risk_model.getRiskProfile(30).toDict()
        snake_keys = [k for k in d.keys() if "_" in k]
        assert snake_keys == [], f"Ditemukan snake_case keys: {snake_keys}"


class TestCompareAges:
    """Unit tests untuk compareAges()."""

    def test_compare_returns_correct_structure(self, risk_model):
        result = risk_model.compareAges(25, 40)
        assert "ageA" in result
        assert "ageB" in result
        assert "riskRatioAToB" in result
        assert "interpretation" in result

    def test_older_age_has_higher_risk(self, risk_model):
        result = risk_model.compareAges(25, 40)
        assert result["riskRatioAToB"] > 1.0

    def test_ratio_25_vs_40_approx_20x(self, risk_model):
        """
        Rasio risiko usia 40 vs 25 sekitar 19.75x.
        Sesuai tabel Hook 1981 (0.0395 / 0.0020 = 19.75).
        https://pubmed.ncbi.nlm.nih.gov/6455611/
        """
        result = risk_model.compareAges(25, 40)
        assert 15.0 < result["riskRatioAToB"] < 25.0

    def test_same_age_ratio_is_one(self, risk_model):
        result = risk_model.compareAges(30, 30)
        assert abs(result["riskRatioAToB"] - 1.0) < 0.01
