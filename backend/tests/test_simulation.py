"""
test_simulation.py
==================
Unit test untuk modul simulasi Monte Carlo dan model risiko.
Jalankan dengan: pytest backend/tests/test_simulation.py -v
"""

import pytest
from backend.src.models.chromosome import Chromosome, ChromosomeType, ChromosomeState, ChromosomePair
from backend.src.models.gamete import Gamete, GameteSex, AneuploidyType
from backend.src.models.risk_model import MaternalAgeRiskModel
from backend.src.simulation.monte_carlo import (
    MeiosisMonteCarloSimulator, SimulationConfig
)


class TestChromosome:
    """Test unit untuk model Chromosome."""

    def test_chromosome_label_auto_assign(self):
        """Kromosom tanpa label harus assign otomatis."""
        c = Chromosome(number=21)
        assert c.label == "chr21"

    def test_mark_nondisjunction_meiosis_I(self):
        """Kromosom harus ter-mark ND Meiosis I dengan benar."""
        c = Chromosome(number=21)
        c.markNondisjunction(1)
        assert c.state == ChromosomeState.NONDISJUNCTION_MI

    def test_mark_nondisjunction_invalid_stage(self):
        """Stage meiosis invalid harus raise ValueError."""
        c = Chromosome(number=21)
        with pytest.raises(ValueError):
            c.markNondisjunction(3)

    def test_sex_chromosome_detection(self):
        """Kromosom seks harus terdeteksi dengan benar."""
        x = Chromosome(number=23, chrType=ChromosomeType.SEX_X)
        auto = Chromosome(number=1)
        assert x.isSexChromosome() is True
        assert auto.isSexChromosome() is False


class TestGamete:
    """Test unit untuk model Gamete."""

    def _make_normal_gamete(self) -> Gamete:
        """Helper: buat gamet normal 23 kromosom."""
        chromosomes = [Chromosome(number=i) for i in range(1, 23)]
        chromosomes.append(Chromosome(number=23, chrType=ChromosomeType.SEX_X))
        return Gamete(gameteId="test_egg", sex=GameteSex.EGG, chromosomes=chromosomes, sourceAge=30)

    def test_normal_gamete_not_aneuploid(self):
        """Gamet 23 kromosom tidak boleh terdeteksi aneuploid."""
        g = self._make_normal_gamete()
        assert g.isAneuploid() is False

    def test_aneuploid_gamete_detection(self):
        """Gamet dengan 24 kromosom harus terdeteksi aneuploid."""
        chromosomes = [Chromosome(number=i) for i in range(1, 23)]
        # Tambah kromosom 21 ekstra (Trisomi 21)
        chromosomes.append(Chromosome(number=21))
        chromosomes.append(Chromosome(number=23, chrType=ChromosomeType.SEX_X))
        g = Gamete(gameteId="nd_egg", sex=GameteSex.EGG, chromosomes=chromosomes, sourceAge=38)
        assert g.isAneuploid() is True

    def test_predict_syndrome_down(self):
        """Gamet dengan dua kromosom 21 harus prediksi Sindrom Down."""
        chromosomes = [Chromosome(number=i) for i in range(1, 23)]
        chromosomes.append(Chromosome(number=21))  # ekstra chr21
        chromosomes.append(Chromosome(number=23, chrType=ChromosomeType.SEX_X))
        g = Gamete(gameteId="down_egg", sex=GameteSex.EGG, chromosomes=chromosomes, sourceAge=38)
        syndrome = g.predictSyndrome()
        assert syndrome is not None
        assert "Down" in syndrome or "21" in syndrome

    def test_normal_gamete_no_syndrome(self):
        """Gamet normal tidak boleh menghasilkan prediksi sindrom."""
        g = self._make_normal_gamete()
        assert g.predictSyndrome() is None


class TestRiskModel:
    """Test unit untuk MaternalAgeRiskModel."""

    def setup_method(self):
        self.model = MaternalAgeRiskModel()

    def test_risk_increases_with_age(self):
        """Risiko harus meningkat seiring bertambahnya usia."""
        risk_25 = self.model.interpolateRisk(25)
        risk_40 = self.model.interpolateRisk(40)
        assert risk_40 > risk_25

    def test_classify_young_age_as_low(self):
        """Usia muda (25) harus dikategorikan risiko rendah."""
        profile = self.model.getRiskProfile(25)
        assert profile.riskCategory == "rendah"

    def test_classify_old_age_as_very_high(self):
        """Usia tua (45) harus dikategorikan sangat tinggi."""
        profile = self.model.getRiskProfile(45)
        assert profile.riskCategory == "sangat tinggi"

    def test_risk_curve_length(self):
        """Kurva usia 20-40 harus menghasilkan 21 titik data."""
        curve = self.model.getRiskCurve(ageRange=(20, 40))
        assert len(curve) == 21


class TestMonteCarloSimulator:
    """Test integrasi untuk MeiosisMonteCarloSimulator."""

    def test_simulation_runs_successfully(self):
        """Simulasi 100 iterasi harus berjalan tanpa error."""
        config = SimulationConfig(maternalAge=35, nSimulations=100, randomSeed=42)
        sim = MeiosisMonteCarloSimulator(config)
        result = sim.run()
        assert result.totalRuns == 100

    def test_total_equals_aneuploid_plus_normal(self):
        """Jumlah aneuploid + normal harus sama dengan total runs."""
        config = SimulationConfig(maternalAge=30, nSimulations=200, randomSeed=0)
        sim = MeiosisMonteCarloSimulator(config)
        result = sim.run()
        assert result.aneuploidCount + result.normalCount == result.totalRuns

    def test_older_age_higher_aneuploid_rate(self):
        """Usia lebih tua harus menghasilkan lebih banyak aneuploid (statistik)."""
        cfg_young = SimulationConfig(maternalAge=25, nSimulations=5000, randomSeed=42)
        cfg_old = SimulationConfig(maternalAge=42, nSimulations=5000, randomSeed=42)
        res_young = MeiosisMonteCarloSimulator(cfg_young).run()
        res_old = MeiosisMonteCarloSimulator(cfg_old).run()
        assert res_old.observedRisk > res_young.observedRisk

    def test_reproducible_with_seed(self):
        """Simulasi dengan seed sama harus menghasilkan hasil identik."""
        config1 = SimulationConfig(maternalAge=35, nSimulations=500, randomSeed=99)
        config2 = SimulationConfig(maternalAge=35, nSimulations=500, randomSeed=99)
        r1 = MeiosisMonteCarloSimulator(config1).run()
        r2 = MeiosisMonteCarloSimulator(config2).run()
        assert r1.aneuploidCount == r2.aneuploidCount
