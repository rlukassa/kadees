"""
test_gamete.py
==============
Unit tests untuk model Gamete dan prediksi sindrom klinis.

Memverifikasi bahwa prediksi sindrom konsisten dengan referensi klinis
OMIM dan data tabel Hook 1981.

Sumber:
  OMIM: https://www.omim.org/
  Hassold T, Hunt P (2001). https://pubmed.ncbi.nlm.nih.gov/11283700/
"""

import pytest
from backend.src.models.gamete import Gamete, GameteSex, AneuploidyType
from backend.src.models.chromosome import Chromosome, ChromosomeType, ChromosomeState


def _make_gamete(chromosome_numbers: list, label_suffix: str = "") -> Gamete:
    """Helper: buat gamet dengan kromosom sesuai list nomor."""
    chromosomes = []
    for num in chromosome_numbers:
        ctype = ChromosomeType.SEX_X if num == 23 else ChromosomeType.AUTOSOME
        chromosomes.append(Chromosome(number=num, chrType=ctype, label=f"chr{num}{label_suffix}"))
    return Gamete(gameteId=f"g_{label_suffix}", sex=GameteSex.EGG,
                  chromosomes=chromosomes, sourceAge=30)


def _normal_set() -> list:
    """23 kromosom normal: 1-22 autosom + kromosom seks (23)."""
    return list(range(1, 24))  # 1 sampai 23


class TestIsAneuploid:

    def test_normal_gamete_23_chromosomes(self):
        g = _make_gamete(_normal_set())
        assert not g.isAneuploid()
        assert g.chromosomeCount == 23

    def test_trisomy_gamete_24_chromosomes(self):
        nums = _normal_set() + [21]  # dua salinan kromosom 21
        g = _make_gamete(nums)
        assert g.isAneuploid()
        assert g.chromosomeCount == 24

    def test_monosomy_gamete_22_chromosomes(self):
        nums = [i for i in _normal_set() if i != 21]  # hilangkan kromosom 21
        g = _make_gamete(nums)
        assert g.isAneuploid()
        assert g.chromosomeCount == 22


class TestGetAneuploidyType:

    def test_normal_type(self):
        g = _make_gamete(_normal_set())
        assert g.getAneuploidyType(21) == AneuploidyType.NORMAL

    def test_disomy_type(self):
        """Gamet dengan 2 salinan kromosom 21 → DISOMY (→ trisomi di zigot)."""
        nums = _normal_set() + [21]
        g = _make_gamete(nums)
        assert g.getAneuploidyType(21) == AneuploidyType.DISOMY

    def test_nullisomy_type(self):
        """Gamet tanpa kromosom 21 → NULLISOMY."""
        nums = [i for i in _normal_set() if i != 21]
        g = _make_gamete(nums)
        assert g.getAneuploidyType(21) == AneuploidyType.NULLISOMY


class TestPredictSyndrome:

    def test_normal_gamete_returns_none(self):
        g = _make_gamete(_normal_set())
        assert g.predictSyndrome() is None

    def test_trisomy21_predicted_down(self):
        """
        Gamet dengan 2 salinan chr21 → Trisomi 21 (Sindrom Down).
        OMIM #190685: https://www.omim.org/entry/190685
        """
        nums = _normal_set() + [21]
        g = _make_gamete(nums)
        syndrome = g.predictSyndrome()
        assert syndrome is not None
        assert "21" in syndrome or "Down" in syndrome

    def test_trisomy18_predicted_edwards(self):
        """
        Gamet dengan 2 salinan chr18 → Trisomi 18 (Sindrom Edwards).
        OMIM #601677: https://www.omim.org/entry/601677
        """
        nums = _normal_set() + [18]
        g = _make_gamete(nums)
        syndrome = g.predictSyndrome()
        assert syndrome is not None
        assert "18" in syndrome or "Edwards" in syndrome

    def test_trisomy13_predicted_patau(self):
        """
        Gamet dengan 2 salinan chr13 → Trisomi 13 (Sindrom Patau).
        OMIM #264480: https://www.omim.org/entry/264480
        """
        nums = _normal_set() + [13]
        g = _make_gamete(nums)
        syndrome = g.predictSyndrome()
        assert syndrome is not None
        assert "13" in syndrome or "Patau" in syndrome

    def test_monosomy_x_predicted_turner(self):
        """
        Gamet tanpa kromosom seks (chr23) → Monosomi X (Sindrom Turner).
        OMIM #312750: https://www.omim.org/entry/312750
        """
        nums = [i for i in _normal_set() if i != 23]
        g = _make_gamete(nums)
        syndrome = g.predictSyndrome()
        assert syndrome is not None
        assert "Turner" in syndrome or "45" in syndrome or "Monosomi X" in syndrome

    def test_unclassified_aneuploidy_returns_string(self):
        """Aneuploidi yang tidak terklasifikasi harus mengembalikan string (bukan None)."""
        nums = _normal_set() + [5]  # trisomi 5 — letal, tidak di SYNDROME_MAP utama
        g = _make_gamete(nums)
        syndrome = g.predictSyndrome()
        assert syndrome is not None
        assert isinstance(syndrome, str)


class TestToDict:

    def test_all_keys_camel_case(self):
        g = _make_gamete(_normal_set())
        d = g.toDict()
        snake_keys = [k for k in d.keys() if "_" in k]
        assert snake_keys == [], f"snake_case keys: {snake_keys}"

    def test_normal_gamete_is_aneuploid_false(self):
        g = _make_gamete(_normal_set())
        d = g.toDict()
        assert d["isAneuploid"] is False
        assert d["predictedSyndrome"] is None

    def test_aneuploid_gamete_is_aneuploid_true(self):
        nums = _normal_set() + [21]
        g = _make_gamete(nums)
        d = g.toDict()
        assert d["isAneuploid"] is True
        assert d["predictedSyndrome"] is not None

    def test_chromosome_count_correct(self):
        g = _make_gamete(_normal_set())
        assert g.toDict()["chromosomeCount"] == 23


class TestGetAffectedChromosomes:

    def test_normal_gamete_no_affected(self):
        g = _make_gamete(_normal_set())
        assert len(g.getAffectedChromosomes()) == 0

    def test_nd_chromosome_detected(self):
        """Kromosom yang di-mark ND harus terdeteksi sebagai affected."""
        nums = _normal_set() + [21]
        g = _make_gamete(nums)
        # Tandai kromosom 21 sebagai ND Meiosis I
        for c in g.chromosomes:
            if c.number == 21:
                c.markNondisjunction(1)
                break
        affected = g.getAffectedChromosomes()
        assert len(affected) >= 1
        assert any(c.number == 21 for c in affected)
