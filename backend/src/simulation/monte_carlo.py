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
                "maternalAge":       self.config.maternalAge,
                "nSimulations":      self.config.nSimulations,
                "targetChromosome":  self.config.targetChromosome,
                "gameteSex":         self.config.gameteSex.value,
                "randomSeed":        self.config.randomSeed,
            },
            "results": {
                "totalRuns":             self.totalRuns,
                "aneuploidCount":        self.aneuploidCount,
                "normalCount":           self.normalCount,
                "observedRisk":          round(self.observedRisk, 6),
                "observedRiskPercent":   round(self.observedRisk * 100, 4),
                "modelRisk":             round(self.modelRisk, 6),
                "modelRiskPercent":      round(self.modelRisk * 100, 4),
                "ndMeiosisICount":       self.ndMeiosisICount,
                "ndMeiosisIICount":      self.ndMeiosisIICount,
                "syndromeCounts":        self.syndromeCounts,
                "executionTimeMs":       round(self.executionTimeMs, 2),
                "wilsonCI":              wilsonCI.toDict() if wilsonCI else None,
                "modelValidation":       modelValidation,
            },
            "sampleGametes": [g.toDict() for g in self.sampleGametes],
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

    def _simulateMeiosis(self, pairs: List[ChromosomePair]) -> Gamete:
        gameteChromosomes = []
        ndMeiosisI = False
        ndMeiosisII = False

        for pair in pairs:
            pNd = self._riskProfile.totalRisk
            roll = self._rng.random()

            if roll < pNd:
                # Non-disjunction terjadi → tentukan di Meiosis I atau II
                if self._rng.random() < MEIOSIS_I_FRACTION:
                    # Non-disjunction Meiosis I: KEDUA kromosom masuk ke gamet
                    pair.paternal.markNondisjunction(1)
                    pair.maternal.markNondisjunction(1)
                    gameteChromosomes.extend([pair.paternal, pair.maternal])
                    ndMeiosisI = True
                else:
                    # Non-disjunction Meiosis II: satu kromosom duplikat, satunya hilang
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
                # Normal: pilih satu kromosom secara acak (Hukum Segregasi Mendel)
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
            # Buat sel diploid baru tiap iterasi
            pairs = self._createDiploidCell()

            # Simulasikan meiosis
            gamete, ndMeiosisI, ndMeiosisII = self._simulateMeiosis(pairs)
            gamete.simulationRun = runIndex

            result.totalRuns += 1

            if gamete.isAneuploid():
                result.aneuploidCount += 1
                if ndMeiosisI:
                    result.ndMeiosisICount += 1
                if ndMeiosisII:
                    result.ndMeiosisIICount += 1

                # Catat sindrom
                syndrome = gamete.predictSyndrome() or "Tidak terklasifikasi"
                syndromeCounts[syndrome] = syndromeCounts.get(syndrome, 0) + 1

                # Simpan sampel (maks 5 untuk visualisasi Three.js)
                if len(sampleAneuploid) < 5:
                    sampleAneuploid.append(gamete)
            else:
                result.normalCount += 1

        # Hitung risiko empiris dari simulasi
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
                "observedRisk": res.observedRisk,
                "modelRisk": res.modelRisk,
                "aneuploidCount": res.aneuploidCount,
                "totalRuns": res.totalRuns,
            })
        return results
