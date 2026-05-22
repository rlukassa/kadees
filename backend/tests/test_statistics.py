"""
test_statistics.py
==================
Unit tests untuk SimulationStatisticsAnalyzer.

Memverifikasi Wilson Score CI, Relative Risk, dan statistik deskriptif
yang digunakan dalam laporan ilmiah.

Referensi metode statistik:
  Wilson EB (1927). Probable inference, the law of succession, and
  statistical inference. J. American Statistical Association, 22, 209-212.

  Metropolis N, Ulam S (1949). The Monte Carlo method.
  Journal of the American Statistical Association, 44(247), 335-341.
  https://doi.org/10.1080/01621459.1949.10483310
"""

import pytest
import math
from backend.src.simulation.statistics import SimulationStatisticsAnalyzer, ConfidenceInterval


@pytest.fixture
def analyzer():
    return SimulationStatisticsAnalyzer([])


class TestWilsonConfidenceInterval:
    """Unit tests untuk Wilson Score Confidence Interval."""

    def test_basic_ci_contains_true_proportion(self, analyzer):
        """Wilson CI 95% harus mencakup proporsi observasi."""
        ci = analyzer.wilsonConfidenceInterval(successes=50, n=1000, confidence=0.95)
        p_hat = 50 / 1000
        assert ci.lower <= p_hat <= ci.upper

    def test_ci_lower_less_than_upper(self, analyzer):
        ci = analyzer.wilsonConfidenceInterval(successes=10, n=500)
        assert ci.lower < ci.upper

    def test_ci_bounds_in_valid_range(self, analyzer):
        """Batas CI harus selalu antara 0 dan 1."""
        for s, n in [(0, 100), (1, 100), (99, 100), (100, 100), (5, 1000)]:
            ci = analyzer.wilsonConfidenceInterval(s, n)
            assert 0.0 <= ci.lower <= 1.0
            assert 0.0 <= ci.upper <= 1.0

    def test_zero_successes(self, analyzer):
        """Jika tidak ada sukses, lower CI harus 0."""
        ci = analyzer.wilsonConfidenceInterval(0, 1000)
        assert ci.lower == 0.0
        assert ci.upper > 0.0  # masih ada ketidakpastian ke atas

    def test_all_successes(self, analyzer):
        """Jika semua sukses, upper CI harus 1."""
        ci = analyzer.wilsonConfidenceInterval(1000, 1000)
        assert ci.upper == 1.0

    def test_higher_confidence_gives_wider_interval(self, analyzer):
        """CI 99% harus lebih lebar dari CI 90%."""
        ci90 = analyzer.wilsonConfidenceInterval(100, 1000, 0.90)
        ci99 = analyzer.wilsonConfidenceInterval(100, 1000, 0.99)
        width90 = ci90.upper - ci90.lower
        width99 = ci99.upper - ci99.lower
        assert width99 > width90

    def test_to_dict_returns_camel_case(self, analyzer):
        """toDict() CI harus mengembalikan keys camelCase."""
        ci = analyzer.wilsonConfidenceInterval(50, 1000)
        d = ci.toDict()
        assert "lower" in d
        assert "upper" in d
        assert "center" in d
        assert "levelPercent" in d
        assert "marginOfError" in d
        snake_keys = [k for k in d.keys() if "_" in k]
        assert snake_keys == []

    def test_ci_at_age35_covers_model_risk(self, analyzer):
        """
        Untuk usia 35 (risiko model = 1.05%), simulasi 10.000 iterasi
        seharusnya menghasilkan CI yang mencakup nilai teoritis.
        Validasi berdasarkan laporan: Wilson CI [0.95%, 1.12%].
        """
        # ~105 aneuploid dari 10.000 iterasi pada usia 35 (risiko 1.05%)
        ci = analyzer.wilsonConfidenceInterval(successes=103, n=10_000, confidence=0.95)
        model_risk = 0.0105
        # CI harus mencakup nilai model teoritis
        assert ci.lower <= model_risk <= ci.upper, (
            f"Model risk {model_risk} harus berada dalam [{ci.lower:.4f}, {ci.upper:.4f}]"
        )


class TestRelativeRisk:
    """Unit tests untuk perhitungan Relative Risk."""

    def test_same_risk_rr_is_one(self, analyzer):
        rr = analyzer.relativeRisk(0.02, 0.02)
        assert abs(rr - 1.0) < 1e-9

    def test_double_risk_rr_is_two(self, analyzer):
        rr = analyzer.relativeRisk(0.04, 0.02)
        assert abs(rr - 2.0) < 1e-9

    def test_zero_baseline_returns_inf(self, analyzer):
        rr = analyzer.relativeRisk(0.05, 0.0)
        assert rr == float("inf")

    def test_age25_vs_age40_rr_approx_20(self, analyzer):
        """
        RR usia 40 vs 25 ≈ 19.75x (Hook 1981).
        https://pubmed.ncbi.nlm.nih.gov/6455611/
        """
        rr = analyzer.relativeRisk(riskExposed=0.0395, riskBaseline=0.0020)
        assert 15.0 < rr < 25.0


class TestDescriptiveStats:
    """Unit tests untuk statistik deskriptif."""

    def test_simple_mean(self, analyzer):
        stats = analyzer.descriptiveStats([1.0, 2.0, 3.0, 4.0, 5.0])
        assert abs(stats["mean"] - 3.0) < 1e-6

    def test_empty_list_returns_empty(self, analyzer):
        stats = analyzer.descriptiveStats([])
        assert stats == {}

    def test_single_value(self, analyzer):
        stats = analyzer.descriptiveStats([5.0])
        assert stats["mean"] == 5.0
        assert stats["min"] == 5.0
        assert stats["max"] == 5.0
        assert stats["std"] == 0.0

    def test_std_of_uniform_is_zero(self, analyzer):
        stats = analyzer.descriptiveStats([3.0, 3.0, 3.0, 3.0])
        assert stats["std"] == 0.0

    def test_output_has_all_expected_keys(self, analyzer):
        stats = analyzer.descriptiveStats([1.0, 2.0, 3.0])
        for key in ["n", "mean", "median", "std", "min", "max", "q1", "q3", "iqr"]:
            assert key in stats, f"Key '{key}' tidak ditemukan di descriptiveStats output"


class TestCompareObservedVsModel:
    """Unit tests untuk validasi observasi vs model teoritis."""

    def test_converged_below_10_percent(self, analyzer):
        """Perbedaan < 10% harus menghasilkan interpretasi konvergen."""
        result = analyzer.compareObservedVsModel(observed=0.0103, model=0.0105, n=10_000)
        assert "konvergen" in result["interpretation"].lower()

    def test_not_converged_above_10_percent(self, analyzer):
        """Perbedaan > 10% harus menghasilkan interpretasi belum konvergen."""
        result = analyzer.compareObservedVsModel(observed=0.0200, model=0.0105, n=100)
        assert "belum konvergen" in result["interpretation"].lower()

    def test_absolute_difference_correct(self, analyzer):
        result = analyzer.compareObservedVsModel(observed=0.01, model=0.02, n=1000)
        assert abs(result["absoluteDifference"] - 0.01) < 1e-9

    def test_output_camel_case_keys(self, analyzer):
        result = analyzer.compareObservedVsModel(0.01, 0.02, 1000)
        snake_keys = [k for k in result.keys() if "_" in k]
        assert snake_keys == [], f"snake_case keys ditemukan: {snake_keys}"
