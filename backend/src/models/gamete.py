from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from .chromosome import Chromosome, ChromosomeState


class GameteSex(Enum):
    EGG   = "egg"    # Sel telur (oosit) — dari ibu
    SPERM = "sperm"  # Spermatozoa — dari ayah 


class AneuploidyType(Enum):
    NORMAL    = "normal"     # 23 kromosom, gamet normal
    TRISOMY   = "trisomy"    # Kelebihan 1 kromosom (+1 = 24 kromosom → zigot 47)
    MONOSOMY  = "monosomy"   # Kekurangan 1 kromosom (-1 = 22 kromosom → zigot 45)
    NULLISOMY = "nullisomy"  # Kehilangan kedua kromosom homolog (sangat jarang)
    DISOMY    = "disomy"     # Dua kromosom homolog ada di satu gamet (= Trisomi di zigot)


# ─────────────────────────────────────────────────────────────────────────────
# Peta sindrom klinis: { nomor_kromosom: { count_di_gamet: nama_sindrom } }
# Interpretasi: jumlah salinan kromosom abnormal dalam gamet
# dapat menghasilkan aneuploidi tertentu setelah fertilisasi.
#
# Sumber: OMIM (omim.org), Hassold & Hunt (2001) Nature Reviews Genetics
# ─────────────────────────────────────────────────────────────────────────────
SYNDROME_MAP = {
    21: {
        0: "Monosomi 21 (umumnya tidak viabel)",
        2: "Trisomi 21 (Sindrom Down)",
    },
    18: {
        0: "Monosomi 18 (umumnya tidak viabel)",
        2: "Trisomi 18 (Sindrom Edwards)",
    },
    13: {
        0: "Monosomi 13 (umumnya tidak viabel)",
        2: "Trisomi 13 (Sindrom Patau)",
    },
    16: {
        2: "Trisomi 16 (letal; umum pada keguguran trimester pertama)",
    },
    22: {
        2: "Trisomi 22 (umumnya letal; mosaik dapat viabel)",
    },
    8: {
        2: "Trisomi 8 (Sindrom Warkany 2; biasanya mosaik)",
    },
    23: {
        0: "Monosomi X (Sindrom Turner / 45,X)",
        2: "Trisomi kromosom seks (mis. 47,XXY / Klinefelter; 47,XXX / Triple-X)",
        3: "Tetrasomi seks (mis. 48,XXXY atau 48,XXYY pada laki-laki; 48,XXXX pada perempuan)",
    },
}
 
# Trisomi autosom yang umumnya letal/non-viabel pada kondisi non-mosaik
_LETHAL_TRISOMY_RANGE = set(range(1, 8)) | set(range(9, 13)) | {14, 15, 17, 19, 20}


@dataclass
class Gamete:
    gameteId:      str
    sex:           GameteSex
    chromosomes:   List[Chromosome] = field(default_factory=list)
    sourceAge:     int = 25
    simulationRun: int = 0

    @property
    def chromosomeCount(self) -> int:
        return len(self.chromosomes)

    def getAneuploidyType(self, targetChromosome: int) -> AneuploidyType:
        count = sum(1 for c in self.chromosomes if c.number == targetChromosome)
        if count == 0:
            return AneuploidyType.NULLISOMY
        elif count == 1:
            return AneuploidyType.NORMAL
        elif count == 2:
            return AneuploidyType.DISOMY
        else:
            return AneuploidyType.TRISOMY

    def getAffectedChromosomes(self) -> List[Chromosome]:
        return [
            c for c in self.chromosomes
            if c.state in (ChromosomeState.NONDISJUNCTION_MI, ChromosomeState.NONDISJUNCTION_MII)
        ]

    def isAneuploid(self) -> bool:
        return self.chromosomeCount != 23

    
    # Kromosom seks diasumsikan berasal dari gamet ibu (EGG)
    # Gamet dari ayah dianggap normal
    def predictSyndrome(self) -> Optional[str]:
        if not self.isAneuploid():
            return None

        # Hitung distribusi kromosom dalam gamet
        chrCounts: dict[int, int] = {}
        for c in self.chromosomes:
            chrCounts[c.number] = chrCounts.get(c.number, 0) + 1

        for chrNum, count in chrCounts.items():
            if count == 1:
                continue  # Normal untuk kromosom ini

            # Cari di syndrome map
            if chrNum in SYNDROME_MAP:
                syndrome = SYNDROME_MAP[chrNum].get(count)
                if syndrome:
                    return syndrome

        # Cek kromosom yang hilang dari gamet (harusnya ada 23 unik)
        expectedChr = set(range(1, 24))
        presentChr  = set(chrCounts.keys())
        missingChr  = expectedChr - presentChr

        for chrNum in missingChr:
            if chrNum in SYNDROME_MAP and 0 in SYNDROME_MAP[chrNum]:
                return SYNDROME_MAP[chrNum][0]

        for chrNum, count in chrCounts.items():
            if count >= 2 and chrNum in _LETHAL_TRISOMY_RANGE:
                return f"Trisomi {chrNum} (letal — aborsi spontan)"
 
        total = self.chromosomeCount
        if total > 23:
            return "Aneuploidi trisomi tidak terklasifikasi (kemungkinan tidak viabel)"
        else:
            return "Aneuploidi monosomi tidak terklasifikasi (kemungkinan tidak viabel)"

    def toDict(self) -> dict:
        return {
            "gameteId":           self.gameteId,
            "sex":                self.sex.value,
            "chromosomeCount":    self.chromosomeCount,
            "isAneuploid":        self.isAneuploid(),
            "predictedSyndrome":  self.predictSyndrome(),
            "sourceAge":          self.sourceAge,
            "simulationRun":      self.simulationRun,
            "chromosomes":        [c.toDict() for c in self.chromosomes],
            "affectedChromosomes": [c.toDict() for c in self.getAffectedChromosomes()],
        }
