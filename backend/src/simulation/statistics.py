"""
statistics.py
=============
Modul analisis statistik untuk mengolah hasil simulasi Monte Carlo.
Menghasilkan metrik-metrik yang dibutuhkan untuk laporan ilmiah dan visualisasi.
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ConfidenceInterval:
    """
    Interval kepercayaan untuk proporsi (metode Wilson Score).

    Attributes:
        lower   (float) : Batas bawah interval.
        upper   (float) : Batas atas interval.
        center  (float) : Nilai tengah (proporsi terobservasi).
        level   (float) : Level kepercayaan (misal: 0.95 untuk 95%).
    """
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
    """
    Kelas untuk analisis statistik mendalam hasil simulasi Monte Carlo.
    Menghasilkan metrik statistik yang diperlukan untuk laporan ilmiah.
    """

    Z_SCORES = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}  # Z-scores untuk CI

    def __init__(self, results: List[Dict]):
        """
        def __init__(results: List[Dict]) :
        // Inisialisasi analyzer dengan list hasil simulasi Monte Carlo.
        // param results: list of dict dari SimulationResult.to_dict()["results"].
        // output: None.
        // dipakai untuk: inisialisasi sebelum memanggil metode analisis.
        """
        self.results = results

    def wilsonConfidenceInterval(
        self, successes: int, n: int, confidence: float = 0.95
    ) -> ConfidenceInterval:
        """
        def wilsonConfidenceInterval(successes: int, n: int, confidence: float = 0.95) -> ConfidenceInterval :
        // Menghitung interval kepercayaan proporsi dengan metode Wilson Score.
        // Lebih akurat dari metode Wald untuk proporsi kecil (p < 0.1 atau p > 0.9).
        // param successes: jumlah kejadian positif (gamet aneuploid).
        // param n: total observasi (total simulasi).
        // param confidence: level kepercayaan (default 0.95 = 95%).
        // output: objek ConfidenceInterval.
        // dipakai untuk: pelaporan ketidakpastian hasil simulasi di laporan ilmiah.
        """
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
        """
        def relativeRisk(riskExposed: float, riskBaseline: float) -> float :
        // Menghitung Relative Risk (RR) antara kelompok terpapar dan baseline.
        // param riskExposed: risiko pada kelompok yang diteliti (misal: usia 40).
        // param riskBaseline: risiko baseline (misal: usia 25).
        // output: float nilai RR (>1 berarti lebih berisiko).
        // dipakai untuk: interpretasi klinis perbedaan risiko antar kelompok usia.
        """
        return riskExposed / riskBaseline if riskBaseline > 0 else float('inf')

    def descriptiveStats(self, values: List[float]) -> Dict:
        """
        def descriptiveStats(values: List[float]) -> Dict :
        // Menghitung statistik deskriptif dari daftar nilai numerik.
        // param values: list nilai float (misal: daftar risiko dari berbagai usia).
        // output: dict berisi mean, median, std, min, max, dan quartiles.
        // dipakai untuk: ringkasan statistik di laporan ilmiah bagian Hasil & Diskusi.
        """
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
        """
        def compareObservedVsModel(observed: float, model: float, n: int) -> Dict :
        // Membandingkan risiko observasi simulasi dengan risiko teoritis model probabilistik.
        // param observed: risiko empiris dari simulasi Monte Carlo.
        // param model: risiko teoritis dari tabel usia maternal.
        // param n: jumlah total iterasi simulasi.
        // output: dict berisi perbedaan absolut, relatif, dan interpretasinya.
        // dipakai untuk: validasi model dan bagian Analisis di laporan ilmiah.
        """
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
