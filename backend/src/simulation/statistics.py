import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ConfidenceInterval:
    lower: float
    upper: float
    center: float
    level: float = 0.95

    def toDict(self) -> dict:
        return {
            "lower": round(self.lower, 6),
            "upper": round(self.upper, 6),
            "center": round(self.center, 6),
            "levelPercent": round(self.level * 100, 1),
            "marginOfError": round((self.upper - self.lower) / 2, 6),
        }


class SimulationStatisticsAnalyzer:
    Z_SCORES = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}  # Z-scores untuk CI

    def __init__(self, results: List[Dict]):
        self.results = results

    def wilsonConfidenceInterval(
        self, successes: int, n: int, confidence: float = 0.95
    ) -> ConfidenceInterval:
        z = self.Z_SCORES.get(confidence, 1.960)
        pHat = successes / n if n > 0 else 0
        z2 = z ** 2

        center = (pHat + z2 / (2 * n)) / (1 + z2 / n)
        margin = (z / (1 + z2 / n)) * math.sqrt(pHat * (1 - pHat) / n + z2 / (4 * n ** 2))

        return ConfidenceInterval(
            lower=max(0, center - margin),
            upper=min(1, center + margin),
            center=pHat,
            level=confidence,
        )

    def relativeRisk(self, riskExposed: float, riskBaseline: float) -> float:
        return riskExposed / riskBaseline if riskBaseline > 0 else float('inf')

    def descriptiveStats(self, values: List[float]) -> Dict:
        if not values:
            return {}
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / (n - 1) if n > 1 else 0
        std = math.sqrt(variance)
        sortedVals = sorted(values)
        median = sortedVals[n // 2] if n % 2 else (sortedVals[n // 2 - 1] + sortedVals[n // 2]) / 2
        q1 = sortedVals[n // 4]
        q3 = sortedVals[3 * n // 4]

        return {
            "n": n,
            "mean": round(mean, 6),
            "median": round(median, 6),
            "std": round(std, 6),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
            "q1": round(q1, 6),
            "q3": round(q3, 6),
            "iqr": round(q3 - q1, 6),
        }

    def compareObservedVsModel(
        self, observed: float, model: float, n: int
    ) -> Dict:
        absDiff = abs(observed - model)
        relDiff = absDiff / model if model > 0 else 0

        return {
            "observedRisk": round(observed, 6),
            "modelRisk": round(model, 6),
            "absoluteDifference": round(absDiff, 6),
            "relativeDifferencePercent": round(relDiff * 100, 2),
            "nSimulations": n,
            "interpretation": (
                "Simulasi konvergen dengan model teoritis (perbedaan < 10%)"
                if relDiff < 0.10 else
                "Simulasi belum konvergen, pertimbangkan menambah iterasi"
            ),
        }
