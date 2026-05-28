from dataclasses import dataclass
from typing import Dict, List, Tuple
import math


# ═══════════════════════════════════════════════════════════════════════════════
# TABEL RISIKO EMPIRIS
#
# // diambil dari source:
# //   Hook EB (1981). Tabel 1: "All chromosome abnormalities" per usia maternal.
# //   Data amniosentesis >60.000 kehamilan.
# //   https://pubmed.ncbi.nlm.nih.gov/6455611/
# //
# //   Morris JK, Mutton DE, Alberman E (2002).
# //   Revised estimates of the maternal age specific live birth prevalence
# //   of Down's syndrome. Journal of Medical Screening, 9(1), 2-6.
# //   https://doi.org/10.1136/jms.9.1.2
# //   https://pubmed.ncbi.nlm.nih.gov/11943789/
# //
# //   ACMG (2016). Noninvasive prenatal screening for fetal aneuploidy
# //   (position statement). Genetics in Medicine.
# //   https://pubmed.ncbi.nlm.nih.gov/27467454/
#
# Format: { usia_ibu (int) : probabilitas_aneuploidi_total (float 0.0–1.0) }
# Nilai mencakup seluruh kelainan kromosom (trisomi autosom + seks).
# ═══════════════════════════════════════════════════════════════════════════════

MATERNAL_AGE_RISK_TABLE: Dict[int, float] = {
    # Usia muda (15-24): risiko rendah, stabil
    15: 0.0022, 16: 0.0021, 17: 0.0020, 18: 0.0019, 19: 0.0018,
    20: 0.0019, 21: 0.0019, 22: 0.0020, 23: 0.0020, 24: 0.0021,
    # Usia dewasa muda (25-34): risiko meningkat bertahap
    25: 0.0021, 26: 0.0021, 27: 0.0022, 28: 0.0023, 29: 0.0024,
    30: 0.0026, 31: 0.0026, 32: 0.0031, 33: 0.0035, 34: 0.0041,
    # AMA (Advanced Maternal Age) ≥35: peningkatan eksponensial
    35: 0.0056, 36: 0.0067, 37: 0.0081, 38: 0.0095, 39: 0.0124,
    40: 0.0158, 41: 0.0205, 42: 0.0255, 43: 0.0326, 44: 0.0418,
    45: 0.0537, 46: 0.0689, 47: 0.0891, 48: 0.1150, 49: 0.1493,
}

# ─────────────────────────────────────────────────────────────────────────────
# Fraksi non-disjunction per fase meiosis
#
# // diambil dari source:
# //   Hassold T, Hunt P (2001). To err (meiotically) is human: the genesis of
# //   human aneuploidy. Nature Reviews Genetics, 2(4), 280-291.
# //   https://doi.org/10.1038/35066065
# //   https://pubmed.ncbi.nlm.nih.gov/11283700/
# //
# //   Hunt PA, Hassold TJ (2008). Human female meiosis: what makes a good egg
# //   go bad? Trends in Genetics, 24(2), 86-93.
# //   https://doi.org/10.1016/j.tig.2007.11.011
# //   https://pubmed.ncbi.nlm.nih.gov/18262676/
# ─────────────────────────────────────────────────────────────────────────────
MEIOSIS_I_FRACTION:  float = 0.75   # 75% kejadian ND di Meiosis I
MEIOSIS_II_FRACTION: float = 0.25   # 25% kejadian ND di Meiosis II


@dataclass
class RiskProfile:
    maternalAge:     int
    totalRisk:       float
    meiosisIRisk:    float
    meiosisIIRisk:   float
    riskCategory:    str
    riskRatioToBase: float

    def toDict(self) -> dict:
         return {
            "maternal_age":      self.maternalAge,
            "total_risk":        round(self.totalRisk, 6),
            "meiosis_I_risk":     round(self.meiosisIRisk, 6),
            "meiosis_II_risk":    round(self.meiosisIIRisk, 6),
            "risk_category":     self.riskCategory,
            "risk_ratio_to_base":  round(self.riskRatioToBase, 2),
            "total_risk_percent": round(self.totalRisk * 100, 4),
        }


class MaternalAgeRiskModel:
    BASE_AGE: int = 25  # Usia referensi dasar untuk rasio risiko (Hook 1981)

    def __init__(self, customTable: Dict[int, float] = None):
        self._riskTable = customTable if customTable else MATERNAL_AGE_RISK_TABLE.copy()
        self._base_risk = self._riskTable.get(self.BASE_AGE, 0.0021)

    def interpolateRisk(self, age: float) -> float:
        ageFloor = int(math.floor(age))
        ageCeil  = int(math.ceil(age))

        if ageFloor == ageCeil:
            return self._getClampedRisk(ageFloor)

        riskLow  = self._getClampedRisk(ageFloor)
        riskHigh = self._getClampedRisk(ageCeil)
        fraction = age - ageFloor

        # Interpolasi linear: p = p_low + (p_high - p_low) × t
        return riskLow + (riskHigh - riskLow) * fraction

    def _getClampedRisk(self, age: int) -> float:
        minAge  = min(self._riskTable.keys())
        maxAge  = max(self._riskTable.keys())
        clamped = max(minAge, min(maxAge, age))
        return self._riskTable[clamped]

    def classifyRisk(self, probability: float) -> str:
        if probability < 0.005:
            return "rendah"
        elif probability < 0.02:
            return "sedang"
        elif probability < 0.08:
            return "tinggi"
        else:
            return "sangat tinggi"

    def getRiskProfile(self, age: int) -> RiskProfile:
        total        = self.interpolateRisk(age)
        meiosisIRisk = total * MEIOSIS_I_FRACTION
        meiosisIIRisk= total * MEIOSIS_II_FRACTION
        ratio        = total / self._base_risk if self._base_risk > 0 else 1.0

        return RiskProfile(
            maternalAge=age,
            totalRisk=total,
            meiosisIRisk=meiosisIRisk,
            meiosisIIRisk=meiosisIIRisk,
            riskCategory=self.classifyRisk(total),
            riskRatioToBase=ratio,
        )

    def getRiskCurve(self, ageRange: Tuple[int, int] = (15, 49)) -> List[Dict]:
        return [
            self.getRiskProfile(age).toDict()
            for age in range(ageRange[0], ageRange[1] + 1)
        ]

    def compareAges(self, ageA: int, ageB: int) -> Dict:
        profileA = self.getRiskProfile(ageA)
        profileB = self.getRiskProfile(ageB)
        ratio    = (profileB.totalRisk / profileA.totalRisk
                    if profileA.totalRisk > 0 else float("inf"))

        return {
            "age_a":           profileA.toDict(),
            "age_b":           profileB.toDict(),
            "risk_ratio_a_to_b":  round(ratio, 2),
            "interpretation": (
                f"Risiko pada usia {ageB} adalah {ratio:.1f}x lebih tinggi dari usia {ageA}"
            ),
        }
