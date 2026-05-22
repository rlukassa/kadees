# EXAMPLE — Use Cases & Input/Output MeioVis

## Use Case 1: Pemeriksaan Risiko Dasar (Usia Muda)

**Skenario:** Seorang ibu hamil usia **26 tahun** ingin mengetahui risiko aneuploidi kehamilannya.

**Input:**
- Slider Usia: `26 tahun`
- Iterasi: `10.000`
- Kromosom Fokus: `Kromosom 21 (Down)`

**Proses Backend:**
```
GET /api/risk/26
→ MaternalAgeRiskModel.get_risk_profile(26)
→ interpolate_risk(26) = 0.0022 (dari tabel Hook 1981)
→ Meiosis I risk  = 0.0022 × 0.75 = 0.00165
→ Meiosis II risk = 0.0022 × 0.25 = 0.00055
→ Kategori: "rendah" (< 0.5%)
→ Rasio vs usia 25: 1.1×
```

**Output Panel Risiko:**
```
Risiko Total   : 0.2200%
Meiosis I      : 0.0165%
Meiosis II     : 0.0055%
Kategori       : RENDAH
Rasio vs 25th  : 1.1×
```

**Output Three.js:** Animasi sel meiosis berjalan normal. Semua kromosom (biru/cyan) berpisah sempurna. 8 gamet output semuanya hijau (normal).

---

## Use Case 2: Simulasi Monte Carlo Usia AMA (Advanced Maternal Age)

**Skenario:** Ibu hamil usia **38 tahun** ingin simulasi dengan 50.000 iterasi untuk hasil lebih akurat.

**Input:**
- Slider Usia: `38 tahun`
- Iterasi: `50.000`
- Kromosom Fokus: `Kromosom 21 (Down)`

**Proses Backend:**
```
POST /api/simulate
Body: { "maternal_age": 38, "n_simulations": 50000, "target_chromosome": 21 }

→ SimulationConfig terbentuk
→ MeiosisMonteCarloSimulator.run() — loop 50.000×:
   Per iterasi:
   ├── _create_diploid_cell() → 23 ChromosomePair
   ├── roll dice per pasang: random() < 0.0230?
   ├── Jika YA → tentukan Meiosis I (75%) atau II (25%)
   ├── Kromosom duplikat/tidak berpisah masuk ke gamet
   └── Gamete.predict_syndrome() → "Trisomi 21 (Sindrom Down)"
→ SimulationResult: aneuploid=1.150, normal=48.850
```

**Output Panel Hasil:**
```
Gamet Aneuploid  : 1.150
Risiko Observasi : 2.3000%
ND Meiosis I     : 863
ND Meiosis II    : 287
```

**Output Prediksi Sindrom:**
```
🔴 Trisomi 21 (Sindrom Down)     : 720 gamet
🔴 Trisomi 18 (Sindrom Edwards)  : 230 gamet
🔴 Trisomi 13 (Sindrom Patau)    : 115 gamet
🔴 Sindrom Turner / Klinefelter  : 85 gamet
```

**Output Three.js:** Kromosom nomor 21 berwarna **merah berdenyut** saat anafase. Benang spindle merah terlihat gagal menarik. 2 dari 8 gamet output berwarna merah (aneuploid).

---

## Use Case 3: Analisis Age Sweep (Perbandingan Semua Usia)

**Skenario:** Peneliti ingin melihat tren risiko dari usia 20–45 tahun sekaligus.

**Input:**
- Klik tombol `📊 Analisis Semua Usia (20–45)`

**Proses Backend:**
```
GET /api/simulate/sweep?age_min=20&age_max=45&n_sim=500

→ MeiosisMonteCarloSimulator.run_age_sweep(20, 45)
→ Loop 26 usia × 500 iterasi = 13.000 simulasi total
→ Return: [{age:20, observed_risk:0.0015, model_risk:0.0015}, ...]
```

**Output Grafik (Panel Kanan):**
- Line chart memperlihatkan kurva risiko yang naik tajam setelah usia 35
- Titik data berwarna merah untuk usia 35 ke atas (AMA threshold)
- Garis vertikal oranye di usia 35 bertuliskan "AMA Threshold"

**Toast:** `✅ Sweep selesai. 26 titik usia dianalisis.`

---

## Use Case 4: Perbandingan Risiko Dua Usia

**Skenario:** Membandingkan risiko usia 25 vs 40 via API.

**Input (API langsung):**
```
GET /api/risk/compare?age_a=25&age_b=40
```

**Output JSON:**
```json
{
  "age_a": { "maternal_age": 25, "total_risk_percent": 0.2, "risk_category": "rendah" },
  "age_b": { "maternal_age": 40, "total_risk_percent": 3.95, "risk_category": "tinggi" },
  "risk_ratio_a_to_b": 19.75,
  "interpretation": "Risiko pada usia 40 adalah 19.8x lebih tinggi dari usia 25"
}
```

---

## Use Case 5: Visualisasi Non-Disjunction Meiosis II

**Skenario:** Memperlihatkan perbedaan visual ND di Meiosis II (oranye) vs Meiosis I (merah).

**Input:**
- Usia: `42 tahun` (risiko sangat tinggi = 6.9%)
- Iterasi: `10.000`

**Output Three.js:**
- Kromosom berwarna **merah** = ND Meiosis I (kedua kromosom homolog ikut ke satu kutub)
- Kromosom berwarna **oranye** = ND Meiosis II (kromosom saudara tidak berpisah)
- Stage bar chip `Anafase I` berkedip merah saat ND terjadi

---

## Ringkasan Fitur dan I/O

| Fitur | Input | Output |
|---|---|---|
| Profil Risiko | Usia (15–50) | % risiko, kategori, rasio, Meiosis I/II |
| Simulasi Monte Carlo | Usia, N iterasi, chr fokus | Gamet aneuploid, distribusi sindrom, sample gamet |
| Animasi 3D | Hasil simulasi JSON | Animasi sel → kromosom → spindle → gamet |
| Kurva Risiko | Range usia (default 15–50) | Line chart interaktif risiko vs usia |
| Age Sweep | Range usia, N iterasi | Tren risiko observasi vs model teoritis |
| Distribusi ND | Hasil simulasi | Pie chart Meiosis I vs Meiosis II |
| Perbandingan Usia | 2 nilai usia | Rasio RR + interpretasi klinis |

---

## Dataset yang Digunakan

### `maternal_age_risk.csv` — 1.000 baris
Rekaman prenatal sintetis berdasarkan model probabilistik empiris.

| Kolom | Tipe | Contoh |
|---|---|---|
| `patient_id` | string | P0001 |
| `maternal_age` | float | 32.4 |
| `maternal_age_group` | string | 30-34 |
| `gestational_week` | int | 16 |
| `gravida` | int | 2 |
| `test_method` | string | NIPT |
| `trisomy_21_risk` | float | 0.005200 |
| `all_trisomy_risk` | float | 0.005200 |
| `aneuploidy_detected` | int (0/1) | 0 |
| `meiosis_failure_stage` | string | Normal |
| `syndrome_name` | string | (kosong jika normal) |
| `karyotype_result` | string | 46,XX |

### `syndrome_reference.csv` — 37 baris
Referensi medis sindrom kromosom lengkap.

| Kolom | Isi |
|---|---|
| `syndrome_name` | Nama sindrom resmi |
| `chromosome_affected` | Nomor/nama kromosom |
| `type` | Trisomi / Monosomi / Mosaik / Trisomi Seks |
| `aneuploid_karyotype` | Notasi karyotype standar (ISCN) |
| `incidence_per_live_birth` | Frekuensi kejadian klinis |
| `viability` | Viabel / Tidak viable / Mosaik viable |
| `primary_nd_stage` | Meiosis I / Meiosis II / Mitosis |
| `maternal_age_effect` | Kuat / Sedang / Lemah / Tidak ada |
| `clinical_features` | Deskripsi manifestasi klinis |
