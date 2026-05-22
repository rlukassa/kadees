"""
chromosome.py
==============
Modul ini mendefinisikan model domain utama untuk kromosom manusia.
Digunakan sebagai fondasi representasi data kromosom dalam simulasi meiosis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ChromosomeType(Enum):
    """
    Tipe kromosom berdasarkan fungsinya.
    """
    AUTOSOME = "autosome"       # Kromosom non-seks (1-22)
    SEX_X = "X"                 # Kromosom seks X
    SEX_Y = "Y"                 # Kromosom seks Y


class ChromosomeState(Enum):
    """
    Status kromosom selama proses meiosis.
    """
    NORMAL = "normal"               # Pasangan kromosom normal
    NONDISJUNCTION_MI = "nd_mI"    # Gagal pisah di Meiosis I
    NONDISJUNCTION_MII = "nd_mII"  # Gagal pisah di Meiosis II
    MISSING = "missing"             # Kromosom hilang (Monosomi)


@dataclass
class Chromosome:
    """
    Representasi satu kromosom homolog tunggal.

    Attributes:
        number      (int)             : Nomor kromosom (1-22 untuk autosom, atau 23 untuk seks).
        chr_type    (ChromosomeType)  : Jenis kromosom (autosome / X / Y).
        label       (str)             : Label opsional (misal: 'chr21a', 'chr21b').
        state       (ChromosomeState) : Status kromosom (normal / gagal berpisah).
        length_cm   (float)           : Panjang kromosom dalam centimorgan (representasi visual).
    """
    number: int
    chrType: ChromosomeType = ChromosomeType.AUTOSOME
    label: str = ""
    state: ChromosomeState = ChromosomeState.NORMAL
    lengthCm: float = 100.0

    def __post_init__(self):
        # Assign label otomatis jika kosong
        if not self.label:
            self.label = f"chr{self.number}"

    def isSexChromosome(self) -> bool:
        """
        def isSexChromosome() -> bool :
        // Memeriksa apakah kromosom ini adalah kromosom seks.
        // param: tidak ada
        // output: True jika kromosom seks (X atau Y), False jika autosom.
        // dipakai untuk: filter kromosom seks saat analisis aneuploidi seks.
        """
        return self.chrType in (ChromosomeType.SEX_X, ChromosomeType.SEX_Y)

    def markNondisjunction(self, meiosisStage: int) -> None:
        """
        def markNondisjunction(meiosisStage: int) -> None :
        // Menandai kromosom ini mengalami non-disjunction pada tahap meiosis tertentu.
        // param meiosisStage: 1 untuk Meiosis I, 2 untuk Meiosis II.
        // output: None. Mengubah state kromosom secara in-place.
        // dipakai untuk: simulasi kegagalan pemisahan kromosom dalam meiosis.
        """
        if meiosisStage == 1:
            self.state = ChromosomeState.NONDISJUNCTION_MI
        elif meiosisStage == 2:
            self.state = ChromosomeState.NONDISJUNCTION_MII
        else:
            raise ValueError(f"meiosisStage harus 1 atau 2, bukan {meiosisStage}")

    def toDict(self) -> dict:
        """
        def toDict() -> dict :
        // Mengonversi objek Chromosome menjadi dictionary JSON-serializable.
        // param: tidak ada
        // output: dict berisi semua atribut kromosom.
        // dipakai untuk: serialisasi ke API response (FastAPI) dan frontend Three.js.
        """
        return {
            "number": self.number,
            "type": self.chrType.value,
            "label": self.label,
            "state": self.state.value,
            "lengthCm": self.lengthCm,
            "isSex": self.isSexChromosome(),
        }


@dataclass
class ChromosomePair:
    """
    Representasi pasangan kromosom homolog (diploid).
    Satu pasang terdiri dari dua kromosom (paternal dan maternal).

    Attributes:
        paternal  (Chromosome) : Kromosom dari ayah.
        maternal  (Chromosome) : Kromosom dari ibu.
    """
    paternal: Chromosome
    maternal: Chromosome

    @property
    def pairNumber(self) -> int:
        """
        def pairNumber -> int :
        // Mengembalikan nomor pasangan kromosom.
        // param: tidak ada
        // output: integer nomor kromosom dari kromosom paternal.
        // dipakai untuk: identifikasi pasangan kromosom (1-23).
        """
        return self.paternal.number

    def hasNondisjunction(self) -> bool:
        """
        def hasNondisjunction() -> bool :
        // Memeriksa apakah salah satu kromosom dalam pasangan mengalami non-disjunction.
        // param: tidak ada
        // output: True jika ada kromosom dengan state non-disjunction.
        // dipakai untuk: filter pasangan yang bermasalah dalam hasil simulasi.
        """
        ndStates = {ChromosomeState.NONDISJUNCTION_MI, ChromosomeState.NONDISJUNCTION_MII}
        return self.paternal.state in ndStates or self.maternal.state in ndStates

    def toDict(self) -> dict:
        """
        def toDict() -> dict :
        // Mengonversi pasangan kromosom menjadi dictionary JSON-serializable.
        // param: tidak ada
        // output: dict berisi data paternal, maternal, dan status pasangan.
        // dipakai untuk: serialisasi ke API response dan payload frontend.
        """
        return {
            "pairNumber": self.pairNumber,
            "paternal": self.paternal.toDict(),
            "maternal": self.maternal.toDict(),
            "hasNondisjunction": self.hasNondisjunction(),
        }
