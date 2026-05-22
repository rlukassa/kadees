"""
conftest.py — Shared pytest fixtures untuk backend tests MeioVis.
"""
import pytest
from backend.src.models.risk_model import MaternalAgeRiskModel
from backend.src.models.chromosome import Chromosome, ChromosomeType, ChromosomePair
from backend.src.models.gamete import Gamete, GameteSex
from backend.src.simulation.monte_carlo import MeiosisMonteCarloSimulator, SimulationConfig
from backend.src.simulation.statistics import SimulationStatisticsAnalyzer


@pytest.fixture
def risk_model():
    return MaternalAgeRiskModel()


@pytest.fixture
def config_age30():
    return SimulationConfig(maternalAge=30, nSimulations=500, targetChromosome=21, randomSeed=42)


@pytest.fixture
def config_age38():
    return SimulationConfig(maternalAge=38, nSimulations=1000, targetChromosome=21, randomSeed=42)


@pytest.fixture
def simulator_age30(config_age30, risk_model):
    return MeiosisMonteCarloSimulator(config_age30, risk_model)


@pytest.fixture
def normal_gamete():
    """Gamet normal dengan tepat 23 kromosom."""
    chromosomes = [
        Chromosome(number=i, chrType=ChromosomeType.AUTOSOME, label=f"chr{i}")
        for i in range(1, 23)
    ]
    chromosomes.append(Chromosome(number=23, chrType=ChromosomeType.SEX_X, label="chrX"))
    return Gamete(gameteId="test_normal", sex=GameteSex.EGG, chromosomes=chromosomes, sourceAge=30)


@pytest.fixture
def aneuploid_gamete_trisomy21():
    """Gamet aneuploid dengan Trisomi 21 (dua salinan kromosom 21)."""
    chromosomes = [
        Chromosome(number=i, chrType=ChromosomeType.AUTOSOME, label=f"chr{i}")
        for i in range(1, 23)
    ]
    # Tambah satu lagi kromosom 21 → trisomi
    chromosomes.append(Chromosome(number=21, chrType=ChromosomeType.AUTOSOME, label="chr21_dup"))
    chromosomes.append(Chromosome(number=23, chrType=ChromosomeType.SEX_X, label="chrX"))
    return Gamete(gameteId="test_trisomy21", sex=GameteSex.EGG, chromosomes=chromosomes, sourceAge=38)


@pytest.fixture
def analyzer():
    return SimulationStatisticsAnalyzer([])
