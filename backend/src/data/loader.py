import csv
from typing import Dict, List
from pathlib import Path

# Path ke folder data relatif dari file ini (root proyek adalah parents[3])
DATA_RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"

# ─────────────────────────────────────────────────────────────────────────────
# Fallback default jika syndrome_reference.csv tidak ditemukan.
# // diambil dari source:
# //   OMIM (Online Mendelian Inheritance in Man): https://www.omim.org/
# //     MIM #190685 (Trisomi 21 / Down syndrome)
# //     MIM #601677 (Trisomi 18 / Edwards syndrome)
# //     MIM #264480 (Trisomi 13 / Patau syndrome)
# //     MIM #312750 (Monosomi X / Turner syndrome)
# //   ACMG (2016). Noninvasive prenatal screening for fetal aneuploidy.
# //   https://pubmed.ncbi.nlm.nih.gov/27467454/
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_SYNDROME_REFERENCE = [
    {
        "syndromeName":        "Trisomi 21 (Sindrom Down)",
        "chromosomeAffected":  "21",
        "type":                "Trisomi Autosom",
        "aneuploidKaryotype":  "47 XX/XY +21",
        "incidencePerLiveBirth": "1/700-1000",
        "viability":           "Viabel",
        "primaryNdStage":      "Meiosis I/II",
        "maternalAgeEffect":   "Sangat Kuat",
        "clinicalFeatures":    "Disabilitas intelektual ringan-sedang; wajah khas; hipotonia",
    },
    {
        "syndromeName":        "Trisomi 18 (Sindrom Edwards)",
        "chromosomeAffected":  "18",
        "type":                "Trisomi Autosom",
        "aneuploidKaryotype":  "47 XX/XY +18",
        "incidencePerLiveBirth": "1/3000-8000",
        "viability":           "Viabel (singkat)",
        "primaryNdStage":      "Meiosis I",
        "maternalAgeEffect":   "Kuat",
        "clinicalFeatures":    "Cacat jantung berat; IUGR; tangan overlapping; kepala kecil",
    },
    {
        "syndromeName":        "Trisomi 13 (Sindrom Patau)",
        "chromosomeAffected":  "13",
        "type":                "Trisomi Autosom",
        "aneuploidKaryotype":  "47 XX/XY +13",
        "incidencePerLiveBirth": "1/10000-16000",
        "viability":           "Viabel (singkat)",
        "primaryNdStage":      "Meiosis I",
        "maternalAgeEffect":   "Kuat",
        "clinicalFeatures":    "Holoprosensefali; polidaktili; bibir sumbing; cacat jantung berat",
    },
    {
        "syndromeName":        "Monosomi X (Sindrom Turner)",
        "chromosomeAffected":  "X",
        "type":                "Monosomi Seks",
        "aneuploidKaryotype":  "45,X",
        "incidencePerLiveBirth": "1/2500 perempuan",
        "viability":           "Viabel",
        "primaryNdStage":      "Meiosis I/II",
        "maternalAgeEffect":   "Lemah",
        "clinicalFeatures":    "Perawakan pendek; gonadal dysgenesis; infertilitas; pterygium colli",
    },
]


def snakeToCamel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:]) if parts else name


def camelizeDict(row: Dict) -> Dict:
    return {snakeToCamel(key): value for key, value in row.items()}


class DatasetLoader:
    def __init__(self, dataDir: Path = DATA_RAW_DIR):
        self.dataDir = dataDir

    # // diambil dari source: https://embryology.med.unsw.edu.au/embryology/index.php?title=Template:Genetic_risk_maternal_age_table
    def loadMaternalAgeRisk(self) -> Dict[int, float]:
        filePath = self.dataDir / "maternal_age_risk.csv"
        if not filePath.exists():
            raise FileNotFoundError(
                f"maternal_age_risk.csv tidak ditemukan di {filePath}. "
                f"Jalankan: python data/generate_datasets.py"
            )
        resultMap = {}
        with open(filePath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    age  = int(float(row["maternal_age"]))
                    risk = float(row["all_trisomy_risk"])
                    resultMap[age] = risk
                except (ValueError, KeyError):
                    continue
        return resultMap

    # // diambil dari source: https://www.omim.org/entry/190685
    def loadSyndromeReference(self) -> List[Dict]:
        filePath = self.dataDir / "syndrome_reference.csv"
        if not filePath.exists():
            return DEFAULT_SYNDROME_REFERENCE.copy()

        results = []
        with open(filePath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(camelizeDict(dict(row)))
        return results

    # // diambil dari source: https://embryology.med.unsw.edu.au/embryology/index.php?title=Template:Genetic_risk_maternal_age_table
    def loadMaternalAgeRows(self) -> List[Dict]:
        filePath = self.dataDir / "maternal_age_risk.csv"
        if not filePath.exists():
            raise FileNotFoundError(
                f"maternal_age_risk.csv tidak ditemukan di {filePath}. "
                f"Jalankan: python data/generate_datasets.py"
            )
        rows = []
        with open(filePath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                parsedRow = camelizeDict(dict(row))
                # Konversi tipe data numerik
                for key, value in list(row.items()):
                    camelKey = snakeToCamel(key)
                    if value is None or value == "":
                        parsedRow[camelKey] = None
                        continue
                    if key in ("gestational_week", "gravida", "aneuploidy_detected"):
                        try:
                            parsedRow[camelKey] = int(value)
                        except ValueError:
                            parsedRow[camelKey] = value
                    elif key in ("maternal_age", "trisomy_21_risk", "trisomy_18_risk",
                                 "trisomy_13_risk", "all_trisomy_risk"):
                        try:
                            parsedRow[camelKey] = float(value)
                        except ValueError:
                            parsedRow[camelKey] = value
                rows.append(parsedRow)
        return rows
