import csv
from typing import Dict, List
from pathlib import Path

# Folder dataset mentah (relatif dari root proyek)
DATA_RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"

# ─────────────────────────────────────────────────────────────────────────────
# Fallback default jika syndrome_reference.csv tidak ditemukan.
# Referensi utama:
# - OMIM (Down, Edwards, Patau, Turner syndrome)
# - ACMG guideline terkait fetal aneuploidy screening
DEFAULT_SYNDROME_REFERENCE = [
    {
        "syndromeName":        "Trisomi 21 (Sindrom Down)",
        "chromosomeAffected":  "21",
        "type":                "Trisomi Autosom",
        "aneuploidKaryotype":  "47,XX,+21 / 47,XY,+21",
        "incidencePerLiveBirth": "1/700-1000",
        "viability":           "Viabel",
        "primaryNdStage":      "Meiosis I/II",
        "maternalAgeEffect":   "Sangat Kuat",
        "clinicalFeatures":    "Disabilitas intelektual ringan-sedang, wajah khas, hipotonia, risiko ASD, penyakit jantung kongenital 40-50%",
    },
    {
        "syndromeName":        "Trisomi 18 (Sindrom Edwards)",
        "chromosomeAffected":  "18",
        "type":                "Trisomi Autosom",
        "aneuploidKaryotype":  "47,XX,+18 / 47,XY,+18",
        "incidencePerLiveBirth": "1/6000-8000",
        "viability":           "Viabel (singkat)",
        "primaryNdStage":      "Meiosis I",
        "maternalAgeEffect":   "Kuat",
        "clinicalFeatures":    "Kelainan jantung berat, tangan overlapping, kepala kecil, IUGR, 50% meninggal dalam minggu pertama",
    },
    {
        "syndromeName":        "Trisomi 13 (Sindrom Patau)",
        "chromosomeAffected":  "13",
        "type":                "Trisomi Autosom",
        "aneuploidKaryotype":  "47,XX,+13 / 47,XY,+13",
        "incidencePerLiveBirth": "1/10000-20000",
        "viability":           "Viabel (singkat)",
        "primaryNdStage":      "Meiosis I",
        "maternalAgeEffect":   "Kuat",
        "clinicalFeatures":    "Kelainan jantung kongenital, holoprosensefali, polidaktili, bibir sumbing, median survival 7-10 hari",
    },
    {
        "syndromeName":        "Monosomi X (Sindrom Turner)",
        "chromosomeAffected":  "X",
        "type":                "Monosomi Seks",
        "aneuploidKaryotype":  "45,X",
        "incidencePerLiveBirth": "1/2500 kelahiran perempuan",
        "viability":           "Viabel",
        "primaryNdStage":      "Meiosis I/II",
        "maternalAgeEffect":   "Tidak ada",
        "clinicalFeatures":    "Perawakan pendek, gonadal dysgenesis, infertilitas, pterygium colli, coarctasi aorta, 45-50% dengan mosaik",
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