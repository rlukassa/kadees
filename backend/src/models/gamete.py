"""
gamete.py
=========
Modul ini mendefinisikan model gamet (sel kelamin) hasil proses meiosis.
Gamet bisa normal (haploid 23 kromosom) atau aneuploid (jumlah kromosom abnormal).

Semua atribut, properti, dan output to_dict() menggunakan konvensi camelCase
sesuai BACKEND.md.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from .chromosome import Chromosome, ChromosomeState


class GameteSex(Enum):
    """Jenis gamet berdasarkan sel kelamin."""
    EGG   = "egg"    # Sel telur (oosit) — dari ibu
    SPERM = "sperm"  # Spermatozoa — dari ayah


class AneuploidyType(Enum):
    """
    Tipe kelainan aneuploidi yang dapat dihasilkan dari non-disjunction.
    Berdasarkan terminologi medis standar (ISCN/ACMG).
    """
    NORMAL    = "normal"     # 23 kromosom, gamet normal
    TRISOMY   = "trisomy"    # Kelebihan 1 kromosom (+1 = 24 kromosom → zigot 47)
    MONOSOMY  = "monosomy"   # Kekurangan 1 kromosom (-1 = 22 kromosom → zigot 45)
    NULLISOMY = "nullisomy"  # Kehilangan kedua kromosom homolog (sangat jarang)
    DISOMY    = "disomy"     # Dua kromosom homolog ada di satu gamet (= Trisomi di zigot)


# ─────────────────────────────────────────────────────────────────────────────
# Peta sindrom klinis: { nomor_kromosom: { count_di_gamet: nama_sindrom } }
# Interpretasi: jika gamet memiliki `count` salinan kromosom X, setelah
# dibuahi sperma normal (1 salinan), zigot akan mengalami sindrom terkait.
#
# Sumber: OMIM, ACMG (2016), Hook EB (1981), Hassold & Hunt (2001)
# ─────────────────────────────────────────────────────────────────────────────
SYNDROME_MAP = {
    # Autosom
    21: {
        0: "Monosomi 21 Parsial (tidak viabel)",
        2: "Trisomi 21 (Sindrom Down)",
    },
    18: {
        0: "Monosomi 18 (tidak viabel)",
        2: "Trisomi 18 (Sindrom Edwards)",
    },
    13: {
        0: "Monosomi 13 (tidak viabel)",
        2: "Trisomi 13 (Sindrom Patau)",
    },
    16: {
        2: "Trisomi 16 (letal — penyebab keguguran tersering)",
    },
    22: {
        2: "Trisomi 22 (Cat Eye Syndrome / mosaik)",
    },
    8:  {
        2: "Trisomi 8 (Sindrom Warkany 2 — mosaik viabel)",
    },
    # Kromosom seks (nomor 23 dalam representasi internal kita = kromosom X/Y)
    23: {
        0: "Monosomi X (Sindrom Turner / 45,X)",
        2: "Trisomi Seks — Klinefelter (47,XXY) atau Triple-X (47,XXX)",
        3: "Tetrasomi Seks — 48,XXXY atau 48,XXXX",
    },
}

# Kromosom yang tidak termasuk map → fallback berdasarkan jumlah total gamet
_LETHAL_TRISOMY_RANGE = set(range(1, 13)) | {14, 15, 17, 19, 20}


@dataclass
class Gamete:
    """
    Representasi satu sel gamet hasil meiosis.

    Attributes:
        gameteId       (str)           : Identifikasi unik gamet (misal: "egg_001").
        sex            (GameteSex)     : Jenis gamet (sel telur / sperma).
        chromosomes    (List[Chromosome]) : Daftar kromosom yang dimiliki gamet.
        sourceAge      (int)           : Usia ibu saat produksi gamet.
        simulationRun  (int)           : ID run simulasi Monte Carlo.
    """
    gameteId:      str
    sex:           GameteSex
    chromosomes:   List[Chromosome] = field(default_factory=list)
    sourceAge:     int = 25
    simulationRun: int = 0

    @property
    def chromosomeCount(self) -> int:
        """
        Menghitung jumlah kromosom total dalam gamet ini.
        Normal = 23 kromosom haploid.
        """
        return len(self.chromosomes)

    def getAneuploidyType(self, targetChromosome: int) -> AneuploidyType:
        """
        def getAneuploidyType(targetChromosome: int) -> AneuploidyType :
        // Menentukan tipe aneuploidi pada nomor kromosom tertentu dalam gamet ini.
        // param targetChromosome: nomor kromosom yang dicek (misal: 21 untuk Down syndrome).
        // output: AneuploidyType (NORMAL, TRISOMY, MONOSOMY, dll).
        // dipakai untuk: diagnosis tipe kelainan kromosom setelah simulasi selesai.
        """
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
        """
        def getAffectedChromosomes() -> List[Chromosome] :
        // Mengambil daftar kromosom yang mengalami non-disjunction dalam gamet ini.
        // param: tidak ada
        // output: list Chromosome yang state-nya bukan NORMAL.
        // dipakai untuk: visualisasi kromosom bermasalah di Three.js.
        """
        return [
            c for c in self.chromosomes
            if c.state in (ChromosomeState.NONDISJUNCTION_MI, ChromosomeState.NONDISJUNCTION_MII)
        ]

    def isAneuploid(self) -> bool:
        """
        def isAneuploid() -> bool :
        // Memeriksa apakah gamet ini adalah aneuploid (jumlah kromosom != 23).
        // param: tidak ada
        // output: True jika jumlah kromosom != 23.
        // dipakai untuk: statistik Monte Carlo dan filter hasil simulasi.
        """
        return self.chromosomeCount != 23

    def predictSyndrome(self) -> Optional[str]:
        """
        def predictSyndrome() -> Optional[str] :
        // Memprediksi sindrom genetik berdasarkan distribusi kromosom gamet.
        // Asumsi: gamet ini dibuahi sperma/sel telur normal (23 kromosom).
        // Menggunakan SYNDROME_MAP yang bersumber dari OMIM dan ACMG 2016.
        // param: tidak ada
        // output: string nama sindrom, atau None jika gamet normal.
        // dipakai untuk: hasil prediksi klinis di panel UI frontend.
        """
        if not self.isAneuploid():
            return None

        # Hitung distribusi kromosom dalam gamet
        chrCounts: dict[int, int] = {}
        for c in self.chromosomes:
            chrCounts[c.number] = chrCounts.get(c.number, 0) + 1

        # Cek setiap kromosom yang count-nya != 1 (abnormal)
        for chrNum, count in chrCounts.items():
            if count == 1:
                continue  # Normal untuk kromosom ini

            # Cari di syndrome map
            if chrNum in SYNDROME_MAP:
                syndrome = SYNDROME_MAP[chrNum].get(count)
                if syndrome:
                    return syndrome

            # Kromosom yang hilang (count == 0) — cek monosomi
            # (kromosom tidak muncul dalam chrCounts sama sekali berarti count=0)

        # Cek kromosom yang HILANG dari gamet (harusnya ada 23 unik)
        expectedChr = set(range(1, 24))
        presentChr  = set(chrCounts.keys())
        missingChr  = expectedChr - presentChr

        for chrNum in missingChr:
            if chrNum in SYNDROME_MAP and 0 in SYNDROME_MAP[chrNum]:
                return SYNDROME_MAP[chrNum][0]

        # Trisomi pada kromosom letal
        for chrNum, count in chrCounts.items():
            if count >= 2 and chrNum in _LETHAL_TRISOMY_RANGE:
                return f"Trisomi {chrNum} (letal — aborsi spontan)"

        # Fallback: aneuploidi tidak terklasifikasi
        total = self.chromosomeCount
        if total > 23:
            return "Aneuploidi — Trisomi tidak terklasifikasi (kemungkinan tidak viabel)"
        else:
            return "Aneuploidi — Monosomi tidak terklasifikasi (kemungkinan tidak viabel)"

    def toDict(self) -> dict:
        """
        def toDict() -> dict :
        // Mengonversi objek Gamete menjadi dictionary JSON-serializable (camelCase).
        // param: tidak ada
        // output: dict lengkap berisi semua properti gamet.
        // dipakai untuk: API response JSON ke frontend Three.js.
        """
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
