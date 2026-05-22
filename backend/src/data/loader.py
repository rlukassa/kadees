"""
loader.py
=========
Modul untuk memuat dan memproses dataset dari file CSV ke dalam format
yang siap digunakan oleh model risiko dan simulator.

Konvensi: semua key dikembalikan dalam camelCase sesuai BACKEND.md.
"""

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
    """Konversi string snake_case ke camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:]) if parts else name


def camelizeDict(row: Dict) -> Dict:
    """Konversi semua key dict dari snake_case ke camelCase."""
    return {snakeToCamel(key): value for key, value in row.items()}


class DatasetLoader:
    """
    Kelas untuk memuat dataset empiris dari file CSV.

    Methods:
        loadMaternalAgeRisk()  : Memuat tabel risiko usia maternal (Hook 1981).
        loadSyndromeReference() : Memuat referensi sindrom kromosom (OMIM/ACMG).
        loadMaternalAgeRows()  : Memuat semua baris dataset sebagai list of dict.
    """

    def __init__(self, dataDir: Path = DATA_RAW_DIR):
        """
        def __init__(dataDir: Path = DATA_RAW_DIR) :
        // Inisialisasi loader dengan direktori sumber data.
        // param dataDir: path ke folder data/raw.
        // output: None.
        // dipakai untuk: membuat instance sebelum memanggil metode load.
        """
        self.dataDir = dataDir

    # // diambil dari source: https://embryology.med.unsw.edu.au/embryology/index.php?title=Template:Genetic_risk_maternal_age_table
    def loadMaternalAgeRisk(self) -> Dict[int, float]:
        """
        def loadMaternalAgeRisk() -> Dict[int, float] :
        // Memuat dataset risiko aneuploidi per usia maternal dari CSV.
        // param: tidak ada.
        // output: dict {usia_maternal (int): all_trisomy_risk (float)}.
        // dipakai untuk: menginisialisasi MaternalAgeRiskModel dengan data empiris.

        // diambil dari source:
        //   Tabel Kompilasi UNSW Embryology (Hook 1981 / Morris 2002 / Savva 2010):
        //   https://embryology.med.unsw.edu.au/embryology/index.php?title=Template:Genetic_risk_maternal_age_table
        //
        //   Hook EB (1981). Rates of chromosome abnormalities at different maternal ages.
        //   https://pubmed.ncbi.nlm.nih.gov/6455611/
        //
        //   Morris JK, Mutton DE, Alberman E (2002). Revised estimates of the maternal age
        //   specific live birth prevalence of Down's syndrome.
        //   https://doi.org/10.1136/jms.9.1.2
        //   https://pubmed.ncbi.nlm.nih.gov/11943789/
        //
        //   Savva GM, Walker K, Morris JK (2010). Prevalence of trisomies 13 and 18
        //   compared to trisomy 21. Prenatal Diagnosis, 30(1), 57-64.
        //   https://doi.org/10.1002/pd.2403
        //   https://pubmed.ncbi.nlm.nih.gov/19911411/
        //
        //   File: data/raw/maternal_age_risk.csv
        //   (dibangkitkan oleh data/generate_datasets.py dari tabel Hook 1981)
        """
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
        """
        def loadSyndromeReference() -> List[Dict] :
        // Memuat tabel referensi sindrom kromosom dari CSV.
        // param: tidak ada.
        // output: list of dict berisi data setiap sindrom (camelCase keys).
        // Jika file tidak ditemukan, kembalikan DEFAULT_SYNDROME_REFERENCE (4 baris).
        // dipakai untuk: endpoint /api/data/syndromes dan panel info di frontend.

        // diambil dari source:
        //   OMIM (Online Mendelian Inheritance in Man):
        //     Trisomi 21 (Sindrom Down) -> https://www.omim.org/entry/190685
        //     Trisomi 18 (Sindrom Edwards) -> https://www.omim.org/entry/601677
        //     Trisomi 13 (Sindrom Patau) -> https://www.omim.org/entry/264480
        //     Monosomi X (Sindrom Turner) -> https://www.omim.org/entry/312750
        //     Sindrom Klinefelter -> https://www.omim.org/entry/300120
        //     Trisomi X (Triple X) -> https://www.omim.org/entry/300120
        //   ACMG (2016). https://pubmed.ncbi.nlm.nih.gov/27467454/
        //   Hassold T, Hunt P (2001). https://pubmed.ncbi.nlm.nih.gov/11283700/
        //   Alberts B et al. (2015). Molecular Biology of the Cell (6th ed).
        //   https://www.ncbi.nlm.nih.gov/books/NBK21054/
        //   File: data/raw/syndrome_reference.csv (37 baris, sumber OMIM/ACMG)
        """
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
        """
        def loadMaternalAgeRows() -> List[Dict] :
        // Memuat semua baris dari maternal_age_risk.csv sebagai list of dict (camelCase).
        // Berguna untuk endpoint API yang mengembalikan sampel data mentah.
        // param: tidak ada.
        // output: list of dict berisi semua baris rekaman prenatal (camelCase keys).
        // dipakai untuk: endpoint /api/data/maternal-age dan analisis EDA di notebook.

        // diambil dari source:
        //   Tabel Kompilasi UNSW Embryology (Hook 1981 / Morris 2002 / Savva 2010):
        //   https://embryology.med.unsw.edu.au/embryology/index.php?title=Template:Genetic_risk_maternal_age_table
        //
        //   Hook EB (1981). https://pubmed.ncbi.nlm.nih.gov/6455611/
        //   Morris JK et al. (2002). https://pubmed.ncbi.nlm.nih.gov/11943789/
        //   Savva GM et al. (2010). https://pubmed.ncbi.nlm.nih.gov/19911411/
        //   ACMG (2016). https://pubmed.ncbi.nlm.nih.gov/27467454/
        //   File: data/raw/maternal_age_risk.csv
        //   (1000 rekaman prenatal berdasarkan distribusi empiris Hook 1981)
        """
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
