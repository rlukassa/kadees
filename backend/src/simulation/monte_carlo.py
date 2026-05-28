import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from ..models.chromosome import Chromosome, ChromosomeType, ChromosomeState, ChromosomePair
from ..models.gamete import Gamete, GameteSex
from ..models.risk_model import MaternalAgeRiskModel, MEIOSIS_I_FRACTION
from ..simulation.statistics import SimulationStatisticsAnalyzer


@dataclass
class SimulationConfig:
    maternalAge: int = 30
    nSimulations: int = 10_000
    targetChromosome: int = 21
    gameteSex: GameteSex = GameteSex.EGG
    randomSeed: Optional[int] = None


@dataclass
class SimulationResult:
    config: SimulationConfig
    totalRuns: int = 0
    aneuploidCount: int = 0
    normalCount: int = 0
    observedRisk: float = 0.0
    modelRisk: float = 0.0
    ndMeiosisICount: int = 0
    ndMeiosisIICount: int = 0
    syndromeCounts: Dict[str, int] = field(default_factory=dict)
    executionTimeMs: float = 0.0
    sampleGametes: List[Gamete] = field(default_factory=list)

    def toDict(self) -> dict:
        analyzer = SimulationStatisticsAnalyzer([])
        wilsonCI = analyzer.wilsonConfidenceInterval(
            successes=self.aneuploidCount, n=self.totalRuns, confidence=0.95
        ) if self.totalRuns > 0 else None

        modelValidation = analyzer.compareObservedVsModel(
            observed=self.observedRisk, model=self.modelRisk, n=self.totalRuns
        ) if self.totalRuns > 0 else {}

        return {
            "config": {
                "maternal_age":       self.config.maternalAge,
                "n_simulations":      self.config.nSimulations,
                "target_chromosome":  self.config.targetChromosome,
                "gamete_sex":         self.config.gameteSex.value,
                "random_seed":        self.config.randomSeed,
            },
            "results": {
                "total_runs":             self.totalRuns,
                "aneuploid_count":        self.aneuploidCount,
                "normal_count":           self.normalCount,
                "observed_risk":          round(self.observedRisk, 6),
                "observed_risk_percent":   round(self.observedRisk * 100, 4),
                "model_risk":             round(self.modelRisk, 6),
                "model_risk_percent":      round(self.modelRisk * 100, 4),
                "nd_meiosis_I_count":       self.ndMeiosisICount,
                "nd_meiosis_II_count":      self.ndMeiosisIICount,
                "syndrome_counts":        self.syndromeCounts,
                "execution_time_ms":       round(self.executionTimeMs, 2),
                "wilson_ci":              wilsonCI.toDict() if wilsonCI else None,
                "model_validation":       modelValidation,
            },
            "sample_gametes": [g.toDict() for g in self.sampleGametes],
        }


class MeiosisMonteCarloSimulator:

    # Kromosom seks default untuk sel telur (XX) — ovum selalu punya X
    DEFAULT_SEX_CHROMOSOME: ChromosomeType = ChromosomeType.SEX_X

    def __init__(self, config: SimulationConfig, riskModel: MaternalAgeRiskModel = None):
        self.config = config
        self.riskModel = riskModel or MaternalAgeRiskModel()
        self._rng = random.Random(config.randomSeed)
        self._riskProfile = self.riskModel.getRiskProfile(config.maternalAge)

    def _createDiploidCell(self) -> List[ChromosomePair]:
        pairs = []
        for i in range(1, 23):  # Autosom 1–22
            paternal = Chromosome(number=i, chrType=ChromosomeType.AUTOSOME,
                                  label=f"chr{i}p", lengthCm=100.0 - i * 2)
            maternal = Chromosome(number=i, chrType=ChromosomeType.AUTOSOME,
                                  label=f"chr{i}m", lengthCm=100.0 - i * 2)
            pairs.append(ChromosomePair(paternal=paternal, maternal=maternal))

        # Kromosom seks ke-23 (sel telur = XX)
        sexPat = Chromosome(number=23, chrType=ChromosomeType.SEX_X, label="chrXp")
        sexMat = Chromosome(number=23, chrType=ChromosomeType.SEX_X, label="chrXm")
        pairs.append(ChromosomePair(paternal=sexPat, maternal=sexMat))

        return pairs

    def _simulateMeiosis(self, pairs: List[ChromosomePair]):
        gameteChromosomes = []
        ndMeiosisI = False
        ndMeiosisII = False

        # Probabilitas nondisjunction dihitung sekali per pembentukan gamet.
        # Sebelumnya sempat di-roll untuk setiap kromosom sehingga
        # risiko total jadi jauh lebih besar dari seharusnya.
        ndOccurred = self._rng.random() < self._riskProfile.totalRisk

        # Cari kromosom target jika simulasi memang menghasilkan ND.
        # Kalau target tidak ditemukan, pilih pasangan secara acak.
        ndPairIndex = None
        if ndOccurred:
            for i, pair in enumerate(pairs):
                if pair.pairNumber == self.config.targetChromosome:
                    ndPairIndex = i
                    break
            if ndPairIndex is None:
                ndPairIndex = self._rng.randint(0, len(pairs) - 1)

        for i, pair in enumerate(pairs):
            if ndOccurred and i == ndPairIndex:
                # Nondisjunction meiosis I
                if self._rng.random() < MEIOSIS_I_FRACTION:
                    pair.paternal.markNondisjunction(1)
                    pair.maternal.markNondisjunction(1)
                    gameteChromosomes.extend([pair.paternal, pair.maternal])
                    ndMeiosisI = True
                else:
                    # Nondisjunction meiosis II
                    chosen = self._rng.choice([pair.paternal, pair.maternal])
                    duplicate = Chromosome(
                        number=chosen.number, chrType=chosen.chrType,
                        label=chosen.label + "_dup", lengthCm=chosen.lengthCm,
                    )
                    chosen.markNondisjunction(2)
                    duplicate.markNondisjunction(2)
                    gameteChromosomes.extend([chosen, duplicate])
                    ndMeiosisII = True
            else:
                chosen = self._rng.choice([pair.paternal, pair.maternal])
                gameteChromosomes.append(chosen)

        gameteId = f"egg_{self._rng.randint(100000, 999999)}"
        return Gamete(
            gameteId=gameteId,
            sex=self.config.gameteSex,
            chromosomes=gameteChromosomes,
            sourceAge=self.config.maternalAge,
        ), ndMeiosisI, ndMeiosisII

    def run(self) -> SimulationResult:
        startTime = time.perf_counter()

        result = SimulationResult(config=self.config)
        result.modelRisk = self._riskProfile.totalRisk
        syndromeCounts: Dict[str, int] = {}
        sampleAneuploid: List[Gamete] = []

        for runIndex in range(self.config.nSimulations):
            pairs = self._createDiploidCell()

            gamete, ndMeiosisI, ndMeiosisII = self._simulateMeiosis(pairs)
            gamete.simulationRun = runIndex

            result.totalRuns += 1

            if gamete.isAneuploid():
                result.aneuploidCount += 1
                if ndMeiosisI:
                    result.ndMeiosisICount += 1
                if ndMeiosisII:
                    result.ndMeiosisIICount += 1

                syndrome = gamete.predictSyndrome() or "Tidak terklasifikasi"
                syndromeCounts[syndrome] = syndromeCounts.get(syndrome, 0) + 1

                if len(sampleAneuploid) < 5:
                    sampleAneuploid.append(gamete)
            else:
                result.normalCount += 1

        result.observedRisk = result.aneuploidCount / result.totalRuns if result.totalRuns > 0 else 0
        result.syndromeCounts = syndromeCounts
        result.sampleGametes = sampleAneuploid
        result.executionTimeMs = (time.perf_counter() - startTime) * 1000

        return result

    def runAgeSweep(self, ageRange: Tuple[int, int] = (20, 45)) -> List[Dict]:
        results = []
        for age in range(ageRange[0], ageRange[1] + 1):
            cfg = SimulationConfig(
                maternalAge=age,
                nSimulations=self.config.nSimulations // 10,  # Lebih cepat untuk sweep
                targetChromosome=self.config.targetChromosome,
                gameteSex=self.config.gameteSex,
                randomSeed=self.config.randomSeed,
            )
            sim = MeiosisMonteCarloSimulator(cfg, self.riskModel)
            res = sim.run()
            results.append({
                "age": age,
                "observed_risk": res.observedRisk,
                "model_risk": res.modelRisk,
                "aneuploid_count": res.aneuploidCount,
                "total_runs": res.totalRuns,
            })
        return results
