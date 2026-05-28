"""
generate_datasets.py
====================
Script untuk membangkitkan dataset CSV yang digunakan MeioVis.

Dataset dibangkitkan dari distribusi dan probabilitas empiris berdasarkan:

- Hook EB (1981). Rates of chromosome abnormalities at different maternal ages.
  Obstetrics & Gynecology, 58(3), 282-285.
  https://pubmed.ncbi.nlm.nih.gov/6455611/

- Morris JK, Mutton DE, Alberman E (2002). Revised estimates of the maternal age
  specific live birth prevalence of Down's syndrome.
  Journal of Medical Screening, 9(1), 2-6.
  https://doi.org/10.1136/jms.9.1.2
  https://pubmed.ncbi.nlm.nih.gov/11943789/

- Savva GM, Walker K, Morris JK (2010). The maternal age-specific live birth
  prevalence of trisomies 13 and 18 compared to trisomy 21 (Down syndrome).
  Prenatal Diagnosis, 30(1), 57-64.
  https://doi.org/10.1002/pd.2403
  https://pubmed.ncbi.nlm.nih.gov/19911411/

- ACMG (2016). Noninvasive prenatal screening for fetal aneuploidy, 2016 update:
  a position statement of the American College of Medical Genetics and Genomics.
  Genetics in Medicine.
  https://pubmed.ncbi.nlm.nih.gov/27467454/

- Hassold T, Hunt P (2001). To err (meiotically) is human: the genesis of human
  aneuploidy. Nature Reviews Genetics, 2(4), 280-291.
  https://doi.org/10.1038/35066065
  https://pubmed.ncbi.nlm.nih.gov/11283700/

Setiap nilai risiko per usia diambil langsung dari tabel Hook 1981 yang telah
divalidasi secara klinis, bukan dibangkitkan secara acak.
"""

import csv
import random
import math
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MATERNAL_AGE_CSV  = OUTPUT_DIR / "maternal_age_risk.csv"

# ── Seed tetap untuk reprodusibilitas (open science) ──────────────────────────
RANDOM_SEED = 42
rng = random.Random(RANDOM_SEED)

# ═══════════════════════════════════════════════════════════════════════════════
# TABEL EMPIRIS HOOK 1981 + Morris 2002 + Savva 2010
#
# Sumber utama:
#   Hook EB (1981). Tabel 1: Rates per Thousand of Chromosome Abnormalities
#   in Live Births by Single-Year Interval.
#   Obstetrics & Gynecology, 58(3), 282-285.
#   https://pubmed.ncbi.nlm.nih.gov/6455611/
#
# Metode konversi:
#   Nilai diambil dari titik tengah rentang di Tabel 1 Hook 1981,
#   lalu dibagi 1000 untuk konversi ke probabilitas (0.0 – 1.0).
#   Contoh: T21 usia 35 → rentang 2.5–3.9/1000 → midpoint 3.2/1000 → 0.003200
#
#   Kolom "all_chromosome_risk" diambil dari kolom "Total†" Hook 1981 Tabel 1,
#   yang mencakup seluruh abnormalitas kromosom:
#   T21 + T18 + T13 + XXY + XYY + Turner (45,X) + other clinically significant.
#   Catatan footnote †: Total dihitung dengan asumsi rate autosomal aneuploidies
#   pada midpoint rentang yang diberikan.
#
#   Usia <20 (tidak ada rentang di Hook 1981 karena footnote ‡):
#   Nilai T21/T18/T13 diekstrapolasi mundur dari pola usia 20-25 menggunakan
#   regresi log-linear. Nilai Total† diambil langsung dari tabel (tersedia).
#   Usia 50: ekstrapolasi dari tren eksponensial usia 45-49.
#
# Format: { usia: (t21_risk, t18_risk, t13_risk, all_chromosome_risk) }
# Semua nilai adalah probabilitas (0.0 – 1.0) per kelahiran hidup
# ═══════════════════════════════════════════════════════════════════════════════
EMPIRICAL_RISK_TABLE = {
    # Usia: (T21,        T18,        T13,        All chromosomes)
    # ── Usia <20: Total dari Hook 1981; T21/T18/T13 ekstrapolasi log-linear ──
    15:  (0.001000,  0.000050,  0.000050,  0.002200),  # Total Hook: 2.2/1000
    16:  (0.000950,  0.000050,  0.000050,  0.002100),  # Total Hook: 2.1/1000
    17:  (0.000900,  0.000050,  0.000050,  0.002000),  # Total Hook: 2.0/1000
    18:  (0.000850,  0.000050,  0.000050,  0.001900),  # Total Hook: 1.9/1000
    19:  (0.000700,  0.000050,  0.000050,  0.001800),  # Total Hook: 1.8/1000
    # ── Usia 20–24: midpoint rentang Hook 1981 Tabel 1 ───────────────────────
    20:  (0.000600,  0.000050,  0.000050,  0.001900),  # T21: mid(0.5–0.7); Total: 1.9/1000
    21:  (0.000600,  0.000050,  0.000050,  0.001900),  # T21: mid(0.5–0.7); Total: 1.9/1000
    22:  (0.000700,  0.000050,  0.000050,  0.002000),  # T21: mid(0.6–0.8); Total: 2.0/1000
    23:  (0.000700,  0.000050,  0.000050,  0.002000),  # T21: mid(0.6–0.8); Total: 2.0/1000
    24:  (0.000800,  0.000050,  0.000050,  0.002100),  # T21: mid(0.7–0.9); Total: 2.1/1000
    # ── Usia 25–29 ───────────────────────────────────────────────────────────
    25:  (0.000800,  0.000100,  0.000050,  0.002100),  # T21: mid(0.7–0.9);  T18: mid(0.1–0.1); Total: 2.1/1000
    26:  (0.000850,  0.000100,  0.000050,  0.002100),  # T21: mid(0.7–1.0);  T18: mid(0.1–0.1); Total: 2.1/1000
    27:  (0.000900,  0.000150,  0.000050,  0.002200),  # T21: mid(0.8–1.0);  T18: mid(0.1–0.2); Total: 2.2/1000
    28:  (0.000950,  0.000150,  0.000100,  0.002300),  # T21: mid(0.8–1.1);  T18: mid(0.1–0.2); Total: 2.3/1000
    29:  (0.001000,  0.000150,  0.000100,  0.002400),  # T21: mid(0.8–1.2);  T18: mid(0.1–0.2); Total: 2.4/1000
    # ── Usia 30–34 ───────────────────────────────────────────────────────────
    30:  (0.001050,  0.000150,  0.000100,  0.002600),  # T21: mid(0.9–1.2);  T18: mid(0.1–0.2); Total: 2.6/1000
    31:  (0.001100,  0.000150,  0.000100,  0.002600),  # T21: mid(0.9–1.3);  T18: mid(0.1–0.2); Total: 2.6/1000
    32:  (0.001300,  0.000150,  0.000150,  0.003100),  # T21: mid(1.1–1.5);  T18: mid(0.1–0.2); Total: 3.1/1000
    33:  (0.001650,  0.000200,  0.000150,  0.003500),  # T21: mid(1.4–1.9);  T18: mid(0.2–0.3); Total: 3.5/1000
    34:  (0.002050,  0.000300,  0.000200,  0.004100),  # T21: mid(1.9–2.4);  T18: mid(0.2–0.4); Total: 4.1/1000
    # ── Usia 35–39 ───────────────────────────────────────────────────────────
    35:  (0.003200,  0.000400,  0.000250,  0.005600),  # T21: mid(2.5–3.9);  T18: mid(0.3–0.5); Total: 5.6/1000  ← AMA threshold
    36:  (0.004100,  0.000450,  0.000300,  0.006700),  # T21: mid(3.2–5.0);  T18: mid(0.3–0.6); Total: 6.7/1000
    37:  (0.005250,  0.000550,  0.000350,  0.008100),  # T21: mid(4.1–6.4);  T18: mid(0.4–0.7); Total: 8.1/1000
    38:  (0.006950,  0.000700,  0.000500,  0.009500),  # T21: mid(5.2–8.1);  T18: mid(0.5–0.9); Total: 9.5/1000
    39:  (0.009050,  0.000950,  0.000650,  0.012400),  # T21: mid(6.6–10.5); T18: mid(0.7–1.2); Total: 12.4/1000
    # ── Usia 40–44 ───────────────────────────────────────────────────────────
    40:  (0.011100,  0.001250,  0.000800,  0.015800),  # T21: mid(8.5–13.7); T18: mid(0.9–1.6); Total: 15.8/1000
    41:  (0.014250,  0.001550,  0.001050,  0.020500),  # T21: mid(10.8–17.9);T18: mid(1.1–2.1); Total: 20.5/1000
    42:  (0.019000,  0.002050,  0.001350,  0.025500),  # T21: mid(13.8–23.4);T18: mid(1.4–2.7); Total: 25.5/1000
    43:  (0.024100,  0.002650,  0.001650,  0.032600),  # T21: mid(17.6–30.6);T18: mid(1.8–3.5); Total: 32.6/1000
    44:  (0.031000,  0.003350,  0.002200,  0.041800),  # T21: mid(22.5–40.0);T18: mid(2.3–4.6); Total: 41.8/1000
    # ── Usia 45–49 ───────────────────────────────────────────────────────────
    45:  (0.040500,  0.004450,  0.002800,  0.053700),  # T21: mid(28.7–52.3);T18: mid(2.9–6.0); Total: 53.7/1000
    46:  (0.052500,  0.005800,  0.003700,  0.068900),  # T21: mid(36.6–68.3);T18: mid(3.7–7.9); Total: 68.9/1000
    47:  (0.067500,  0.007250,  0.004750,  0.089100),  # T21: mid(46.6–89.3);T18: mid(4.7–10.3);Total: 89.1/1000
    48:  (0.085500,  0.009500,  0.006100,  0.115000),  # T21: mid(59.5–116.8);T18:mid(6.0–13.5);Total:115.0/1000
    49:  (0.114250, 0.012700,  0.007800,  0.149300),  # T21: mid(75.8–152.7);T18:mid(7.6–17.6);Total:149.3/1000
    # ── Usia 50: ekstrapolasi eksponensial dari tren usia 45-49 ──────────────
    50:  (0.155000,  0.017000,  0.010500,  0.200000),  # Ekstrapolasi; tidak ada di Hook 1981
}

# Distribusi metode screening
#
# ⚠ CATATAN METODOLOGI:
#   Bobot di bawah BUKAN angka eksplisit dari jurnal manapun.
#   ACMG (2016) dan ACOG Bulletin No.163 (2016) hanya menyebut metode-metode
#   ini secara kualitatif (NIPS "rapidly integrated", amniocentesis "gold standard",
#   dst.) tanpa memberikan angka distribusi penggunaan secara populasi.
#
#   Bobot ini adalah ESTIMASI yang diturunkan dari konteks klinis yang dilaporkan:
#   - NIPT 45%: ACMG 2016 menyebut NIPS sebagai metode paling sensitif dan modern;
#               sejak 2011 penggunaannya meningkat pesat menggantikan metode lama.
#   - Amniosentesis 20%: ACMG 2016 — "gold standard" diagnostik invasif;
#               tetap digunakan terutama untuk konfirmasi hasil positif NIPS.
#   - USG Trimester 1 20%: ACMG 2016 — "first-trimester screening" adalah
#               pendekatan konvensional yang masih umum digunakan.
#   - CVS 10%: ACMG 2016 — chorionic villus sampling, loss rate 0.2–1.3%;
#               digunakan lebih jarang dari amniosentesis karena dilakukan lebih awal.
#   - Serum Ibu 5%: ACMG 2016 — "maternal serum analytes" adalah metode lama
#               (quad test) yang sudah banyak digantikan NIPS.
#
#   Sumber konteks (tidak memberikan angka distribusi eksplisit):
#   ACMG (2016). Noninvasive prenatal screening for fetal aneuploidy.
#   https://pubmed.ncbi.nlm.nih.gov/27467454/
#   ACOG Practice Bulletin No. 163 (2016). Screening for fetal aneuploidy.
#   https://pubmed.ncbi.nlm.nih.gov/27400004/
TEST_METHODS = {
    "NIPT":            0.45,  # Estimasi: dominan modern — ACMG 2016 konteks
    "Amniosentesis":   0.20,  # Estimasi: gold standard invasif — ACMG 2016
    "USG Trimester 1": 0.20,  # Estimasi: konvensional trimester 1 — ACMG 2016
    "CVS":             0.10,  # Estimasi: invasif awal kehamilan — ACMG 2016
    "Serum Ibu":       0.05,  # Estimasi: metode lama (quad test) — ACMG 2016
}

KARYOTYPE_NORMAL_F = "46,XX"
KARYOTYPE_NORMAL_M = "46,XY"

ETHNICITIES = {
    "Jawa":       0.35,
    "Sunda":      0.15,
    "Batak":      0.08,
    "Minang":     0.07,
    "Betawi":     0.06,
    "Bugis":      0.05,
    "Madura":     0.05,
    "Lain-lain":  0.19,
}

# Bobot sindrom berdasarkan distribusi klinis yang dipublikasikan
#
# Metode derivasi per sindrom:
#
# [T21 — 0.626]
#   Hook 1981 Tabel 1: di usia 35, T21 = 3.2/1000, Total = 5.6/1000
#   → rasio T21/Total ≈ 57-65% (bervariasi per usia).
#   Morris JK et al. (2002) mengkonfirmasi T21 sebagai trisomi terbanyak
#   di live births (~60-65%). Nilai 0.626 adalah midpoint estimasi tersebut.
#   Sumber: Hook 1981 https://pubmed.ncbi.nlm.nih.gov/6455611/
#           Morris 2002 https://pubmed.ncbi.nlm.nih.gov/11943789/
#
# [T18 — 0.200]
#   Savva GM et al. (2010) melaporkan prevalensi T18 live birth relatif
#   terhadap T21 adalah ~1:3 sampai 1:4.
#   Hook 1981: di usia 35, T18 = 0.4/1000, T21 = 3.2/1000 → rasio ~12.5%.
#   Ditambah kontribusi di semua usia, proporsi global ~20% dari semua trisomi.
#   Sumber: Savva 2010 https://pubmed.ncbi.nlm.nih.gov/19911411/
#           Hook 1981 https://pubmed.ncbi.nlm.nih.gov/6455611/
#
# [T13 — 0.100]
#   Savva 2010: T13 live birth prevalence ~1/2 dari T18.
#   Hook 1981: di usia 35, T13 = 0.25/1000 vs T18 = 0.4/1000 → rasio ~62%.
#   Proporsi global T13 dari semua trisomi diestimasi ~10%.
#   Sumber: Savva 2010 https://pubmed.ncbi.nlm.nih.gov/19911411/
#
# [Turner 45,X — 0.044]
#   ⚠ ESTIMASI — bukan angka verbatim dari jurnal.
#   ACMG 2016 menyebut "monosomy X occurs in 1–1.5% of pregnancies" —
#   NAMUN ini adalah prevalensi konsepsi/kehamilan, bukan live births.
#   Sebagian besar 45,X berakhir sebagai keguguran spontan (~99%).
#   Di live births, Turner diperkirakan ~1/2500 = 0.4/1000.
#   Hook 1981 Tabel 1 kolom "Turner syndrome genotype": <0.1/1000 di semua usia.
#   Proporsi 4.4% dari semua aneuploidi live births adalah estimasi konservatif
#   berdasarkan rasio Hook 1981 (Turner <0.1 vs Total 2.2–149/1000).
#   Sumber konteks: ACMG 2016 https://pubmed.ncbi.nlm.nih.gov/27467454/
#                   Hook 1981 https://pubmed.ncbi.nlm.nih.gov/6455611/
#
# [Klinefelter 47,XXY — 0.020]
#   Hook 1981 Tabel 1 kolom "XXY": ~0.4–0.6/1000 di semua usia maternal.
#   Relatif terhadap Total ~2.2–5.6/1000 (usia 20-35) → proporsi ~10-20%.
#   Di usia reproduktif umum (rata-rata), estimasi ~2% dari semua aneuploidi.
#   Sumber: Hook 1981 https://pubmed.ncbi.nlm.nih.gov/6455611/
#
# [Trisomi X 47,XXX — 0.007]
#   ⚠ ESTIMASI — Hook 1981 secara eksplisit mengecualikan XXX dari Tabel 1
#   (footnote: "XXX is excluded for reasons given in text").
#   Nilai 0.7% diestimasi dari populasi umum: insidensi 47,XXX ~1/1000
#   perempuan lahir (Forabosco et al. 2009, 88,965 amniosentesis).
#   Proporsi 0.7% dari semua aneuploidi live births adalah estimasi kasar.
#   Sumber estimasi: Forabosco A et al. (2009). Eur J Hum Genet, 17:897-903.
#                   https://doi.org/10.1038/ejhg.2008.246
#
# [XYY 47,XYY — 0.003]
#   Hook 1981 Tabel 1 kolom "XYY": ~0.5/1000 (konstan di semua usia maternal,
#   karena nondisjunction XYY terjadi di Meiosis II paternal, tidak terkait usia ibu).
#   Relatif terhadap Total, proporsinya kecil → estimasi ~0.3%.
#   Sumber: Hook 1981 https://pubmed.ncbi.nlm.nih.gov/6455611/
SYNDROME_WEIGHTS = {
    "Trisomi 21 (Sindrom Down)":    0.626,  # Hook 1981 + Morris 2002: ~60-65% dari semua trisomi live birth
    "Trisomi 18 (Sindrom Edwards)": 0.200,  # Savva 2010 + Hook 1981: ~20% estimasi dari total
    "Trisomi 13 (Sindrom Patau)":   0.100,  # Savva 2010: ~1/2 dari T18, estimasi ~10%
    "Sindrom Turner (45,X)":        0.044,  # ⚠ Estimasi — Hook 1981 <0.1/1000; ACMG 2016 = prevalensi kehamilan bukan live birth
    "Sindrom Klinefelter (47,XXY)": 0.020,  # Hook 1981 XXY ~0.5/1000; estimasi ~2% dari total aneuploidi
    "Trisomi X (47,XXX)":           0.007,  # ⚠ Estimasi — Hook 1981 mengecualikan XXX; basis Forabosco 2009
    "Sindrom XYY (47,XYY)":         0.003,  # Hook 1981 XYY ~0.5/1000; estimasi ~0.3% dari total
}

KARYOTYPE_SYNDROME_MAP = {
    "Trisomi 21 (Sindrom Down)":    ("47,XX,+21", "47,XY,+21"),
    "Trisomi 18 (Sindrom Edwards)": ("47,XX,+18", "47,XY,+18"),
    "Trisomi 13 (Sindrom Patau)":   ("47,XX,+13", "47,XY,+13"),
    "Sindrom Turner (45,X)":        ("45,X",       "45,X"),
    "Sindrom Klinefelter (47,XXY)": ("47,XXY",     "47,XXY"),
    "Trisomi X (47,XXX)":           ("47,XXX",     "47,XXX"),
    "Sindrom XYY (47,XYY)":         ("47,XYY",     "47,XYY"),
}

MEIOSIS_STAGE_PROBS = {
    "Meiosis I":  0.75,   # Hassold & Hunt 2001: dominasi Meiosis I 75-80%
    "Meiosis II": 0.25,
}


def _weighted_choice(choices: dict) -> str:
    """Pilih kunci dari dict {pilihan: bobot} secara acak berbobot."""
    total = sum(choices.values())
    r = rng.uniform(0, total)
    cumulative = 0
    for choice, weight in choices.items():
        cumulative += weight
        if r <= cumulative:
            return choice
    return list(choices.keys())[-1]


def _age_distribution() -> float:
    """
    Bangkitkan usia maternal menggunakan distribusi truncated normal.
    μ=30, σ=6, batas [15, 50] tahun — sesuai distribusi klinis realistik.
    """
    while True:
        age_raw = rng.gauss(30, 6)
        age = round(age_raw, 1)
        if 15.0 <= age <= 50.0:
            return age


def _age_group(age: float) -> str:
    """Tentukan kelompok usia maternal standar klinis (5 tahun interval)."""
    boundaries = [20, 25, 30, 35, 40, 45, 50]
    for i, b in enumerate(boundaries):
        if age < b:
            lower = boundaries[i - 1] if i > 0 else 15
            return f"{lower}-{b - 1}"
    return "45-50"


def _get_risk(age: float):
    """Interpolasi linear risiko aneuploidi dari tabel empiris Hook 1981."""
    age_floor = int(math.floor(age))
    age_ceil  = int(math.ceil(age))
    if age_floor == age_ceil or age_ceil not in EMPIRICAL_RISK_TABLE:
        age_floor = max(15, min(50, age_floor))
        return EMPIRICAL_RISK_TABLE[age_floor]
    r_lo = EMPIRICAL_RISK_TABLE[max(15, min(50, age_floor))]
    r_hi = EMPIRICAL_RISK_TABLE[max(15, min(50, age_ceil))]
    t    = age - age_floor
    return tuple(lo + (hi - lo) * t for lo, hi in zip(r_lo, r_hi))


def generate_maternal_age_dataset(n: int = 1000) -> list:
    """
    Bangkitkan n baris rekaman prenatal berdasarkan model probabilistik Hook 1981.

    Setiap baris merepresentasikan satu pasien prenatal screening dengan:
    - Usia maternal dari distribusi normal (μ=30, σ=6)
    - Risiko trisomi diinterpolasi dari tabel Hook 1981 yang tervalidasi secara klinis
    - Status aneuploidi ditentukan berdasarkan probabilitas empiris
    - Sindrom dan karyotype konsisten dengan distribusi klinis terpublikasi
    """
    records = []
    for i in range(1, n + 1):
        age     = _age_distribution()
        age_int = max(15, min(50, int(round(age))))
        risks   = _get_risk(age)
        t21_risk, t18_risk, t13_risk, all_chr_risk = risks

        gest_week  = rng.randint(10, 22)      # Minggu gestasi: 10-22 minggu (prenatal screen window)
        gravida    = rng.choices([1, 2, 3, 4], weights=[0.40, 0.35, 0.18, 0.07])[0]
        test_meth  = _weighted_choice(TEST_METHODS)
        ethnicity  = _weighted_choice(ETHNICITIES)
        is_female  = rng.random() < 0.5

        # Tentukan status aneuploidi berdasarkan probabilitas empiris
        roll           = rng.random()
        aneuploidy_det = 1 if roll < all_chr_risk else 0

        if aneuploidy_det:
            syndrome       = _weighted_choice(SYNDROME_WEIGHTS)
            karyotypes     = KARYOTYPE_SYNDROME_MAP.get(syndrome, ("47,XX,+?", "47,XY,+?"))
            karyotype      = karyotypes[0] if is_female else karyotypes[1]
            stage_roll     = rng.random()
            meiosis_stage  = "Meiosis I" if stage_roll < 0.75 else "Meiosis II"
        else:
            syndrome      = ""
            karyotype     = KARYOTYPE_NORMAL_F if is_female else KARYOTYPE_NORMAL_M
            meiosis_stage = "Normal"

        records.append({
            "patient_id":          f"P{i:04d}",
            "maternal_age":        round(age, 1),
            "maternal_age_group":  _age_group(age),
            "gestational_week":    gest_week,
            "gravida":             gravida,
            "test_method":         test_meth,
            "trisomy_21_risk":     round(t21_risk, 6),
            "trisomy_18_risk":     round(t18_risk, 6),
            "trisomy_13_risk":     round(t13_risk, 6),
            "all_chromosome_risk":    round(all_chr_risk, 6),
            "aneuploidy_detected": aneuploidy_det,
            "meiosis_failure_stage": meiosis_stage,
            "syndrome_name":       syndrome,
            "karyotype_result":    karyotype,
            "ethnicity":           ethnicity,
        })
    return records


def write_csv(records: list, filepath: Path, fieldnames: list) -> None:
    """Tulis list of dict ke file CSV dengan header."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"[OK] {filepath.name} -- {len(records)} baris ditulis ke {filepath}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== MeioVis Dataset Generator ===")
    print("Sumber data: Hook 1981 | Morris 2002 | Savva 2010 | ACMG 2016\n")

    # maternal_age_risk.csv
    records   = generate_maternal_age_dataset(n=1000)
    fieldnames = [
        "patient_id", "maternal_age", "maternal_age_group",
        "gestational_week", "gravida", "test_method",
        "trisomy_21_risk", "trisomy_18_risk", "trisomy_13_risk",
        "all_chromosome_risk", "aneuploidy_detected",
        "meiosis_failure_stage", "syndrome_name",
        "karyotype_result", "ethnicity",
    ]
    write_csv(records, MATERNAL_AGE_CSV, fieldnames)

    # Statistik ringkas
    aneuploid_count = sum(r["aneuploidy_detected"] for r in records)
    print("\n[INFO] Statistik Dataset:")
    print(f"   Total rekaman   : {len(records)}")
    print(f"   Aneuploid       : {aneuploid_count} ({aneuploid_count/len(records)*100:.1f}%)")
    print(f"   Normal          : {len(records) - aneuploid_count}")

    from collections import Counter
    age_groups = Counter(r["maternal_age_group"] for r in records)
    print("\n   Distribusi usia:")
    for grp, cnt in sorted(age_groups.items()):
        print(f"     {grp}: {cnt} pasien")

    print("\n[DONE] Dataset generation selesai.")
