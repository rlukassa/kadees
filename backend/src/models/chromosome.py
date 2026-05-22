from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ChromosomeType(Enum):
    AUTOSOME = "autosome"       # Kromosom non-seks (1-22)
    SEX_X = "X"                 # Kromosom seks X
    SEX_Y = "Y"                 # Kromosom seks Y


class ChromosomeState(Enum):
    NORMAL = "normal"               # Pasangan kromosom normal
    NONDISJUNCTION_MI = "nd_mI"    # Gagal pisah di Meiosis I
    NONDISJUNCTION_MII = "nd_mII"  # Gagal pisah di Meiosis II
    MISSING = "missing"             # Kromosom hilang (Monosomi)


@dataclass
class Chromosome:
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
        return self.chrType in (ChromosomeType.SEX_X, ChromosomeType.SEX_Y)

    def markNondisjunction(self, meiosisStage: int) -> None:
        if meiosisStage == 1:
            self.state = ChromosomeState.NONDISJUNCTION_MI
        elif meiosisStage == 2:
            self.state = ChromosomeState.NONDISJUNCTION_MII
        else:
            raise ValueError(f"meiosisStage harus 1 atau 2, bukan {meiosisStage}")

    def toDict(self) -> dict:
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
    paternal: Chromosome
    maternal: Chromosome

    @property
    def pairNumber(self) -> int:
        return self.paternal.number

    def hasNondisjunction(self) -> bool:

        ndStates = {ChromosomeState.NONDISJUNCTION_MI, ChromosomeState.NONDISJUNCTION_MII}
        return self.paternal.state in ndStates or self.maternal.state in ndStates

    def toDict(self) -> dict:
        return {
            "pairNumber": self.pairNumber,
            "paternal": self.paternal.toDict(),
            "maternal": self.maternal.toDict(),
            "hasNondisjunction": self.hasNondisjunction(),
        }
