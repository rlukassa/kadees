# IDEA — MeioVis: Prediksi Aneuploidi Kromosom

## Latar Belakang

Saat proses Meiosis (pembentukan sel telur/sperma), kromosom terkadang gagal berpisah (*Non-disjunction*). Hal ini menyebabkan gamet dengan jumlah kromosom abnormal, yang berujung pada sindrom seperti Sindrom Down (Trisomi 21), Sindrom Patau, atau keguguran. Insiden berkorelasi kuat dengan usia ibu (*maternal age*).

**Pertanyaan Penelitian:**
> Seberapa besar pengaruh usia maternal terhadap probabilitas non-disjunction kromosom pada Meiosis I dan Meiosis II, dan bagaimana distribusinya dapat dimodelkan menggunakan simulasi Monte Carlo?

---

## Alur Kerja Sistem (Workflow)

```
USER INPUT (Browser)
      │
      │  Usia maternal, jumlah iterasi, kromosom fokus
      ▼
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (Vite + Three.js)                             │
│  ─ Slider usia → debounced fetch ke /api/risk/{age}     │
│  ─ Tombol "Jalankan" → POST /api/simulate (JSON body)   │
│  ─ Terima respons JSON → render Three.js + Chart.js     │
└──────────────────────┬──────────────────────────────────┘
                       │  HTTP (localhost:5173 → :8000)
                       ▼
┌─────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI — Python)                             │
│  ─ src/api/main.py → validasi request (Pydantic)        │
│  ─ Panggil MaternalAgeRiskModel → interpolasi risiko    │
│  ─ Panggil MeiosisMonteCarloSimulator → run N iterasi   │
│  ─ Kumpulkan SimulationResult → toDict() → JSON         │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┼──────────────┐
         ▼             ▼              ▼
   risk_model.py  monte_carlo.py  statistics.py
   (Baca tabel     (Loop N kali    (Wilson CI,
    empiris CSV)    per iterasi:    RR, deskriptif)
                    roll dice →
                    gamete terbentuk)
         │
         ▼
  data/raw/maternal_age_risk.csv  (1000 rekaman prenatal)
  data/raw/syndrome_reference.csv (37 sindrom kromosom)

  ═══ NOTEBOOK (Analisis Offline) ═══════════════════════
  notebooks/meiosis_simulation.ipynb
  ─ Load CSV → EDA & statistik deskriptif
  ─ Jalankan simulasi Monte Carlo 10.000 iterasi
  ─ Age sweep 20–45 tahun
  ─ Plot Plotly interaktif & Seaborn heatmap
  ─ Validasi: Observed vs Model Risk
  ─ Wilson Confidence Interval
  ─ Kesimpulan & ekspor hasil ke data/processed/
```

---

## Pembagian Peran Tim (Role per Anggota)

| No | Role | Tanggung Jawab | Deliverable |
|---|---|---|---|
| **1** | **Frontend Dev** | Membangun UI Three.js + Chart.js + CSS glassmorphism. Event handling slider/tombol, integrasi API fetch, animasi GSAP meiosis 3D, visualisasi gamet aneuploid | `frontend/src/` (semua file JS + CSS) |
| **2** | **Backend & Data Engineer** | Membangun FastAPI endpoints, OOP Python (Chromosome, Gamete, RiskModel, Simulator), loader CSV, unit tests | `backend/src/` + `data/generate_datasets.py` + `backend/tests/` |
| **3** | **Data Scientist / Notebook** | EDA dataset, visualisasi Plotly & Seaborn, validasi model statistik, Wilson CI, analisis Relative Risk, interpretasi biologi | `backend/notebooks/meiosis_simulation.ipynb` |
| **4** | **Penulis Laporan / Koordinator** | Menulis laporan ilmiah 6 halaman (Pendahuluan, Metode, Hasil & Diskusi, Kesimpulan), tinjauan pustaka, membuat slide presentasi, koordinasi video 10 menit | `laporan/` + slide + video |

> Setiap anggota tetap memahami keseluruhan sistem karena akan muncul dalam video presentasi.

---

## Fitur Aplikasi Frontend

### Panel Kontrol (Kiri)

| Fitur | Deskripsi |
|---|---|
| **Slider Usia Maternal** | Range 15–50 tahun, real-time update profil risiko dengan debounce 300ms |
| **Pilihan Jumlah Iterasi** | Dropdown: 1.000 / 5.000 / 10.000 / 50.000 iterasi Monte Carlo |
| **Pilihan Kromosom Fokus** | Pilih chr 21 (Down), 18 (Edwards), 13 (Patau), atau X/Y (seks) |
| **Tombol Jalankan Simulasi** | Memicu POST ke API, menampilkan loading overlay, lalu play animasi 3D |
| **Tombol Age Sweep** | Analisis otomatis usia 20–45 tahun sekaligus, hasilnya tampil di grafik |
| **Risk Gauge** | Semi-circular gauge canvas 2D menampilkan % risiko real-time |
| **Profil Risiko Panel** | Tampilkan Risiko Total, Meiosis I, Meiosis II, Kategori, Rasio vs usia 25 |

### Viewport 3D (Tengah)

| Fitur | Deskripsi |
|---|---|
| **Animasi Sel Meiosis GSAP** | Tahap lengkap: Interfase → Profase → Metafase → Anafase → Meiosis II → Gamet |
| **23 Kromosom 3D** | Kapsul 3D merepresentasikan tiap kromosom; kromosom ND berwarna merah berdenyut |
| **Spindle Fiber** | Benang spindle ungu 3D muncul di metafase; merah jika kromosom gagal berpisah |
| **Gamet Hasil** | 8 bola 3D mewakili gamet; proporsi merah = % aneuploid dari simulasi |
| **OrbitControls** | Drag untuk memutar, scroll untuk zoom, auto-rotate setelah animasi selesai |
| **Stage Bar** | Chip label di bawah canvas menandai fase meiosis yang sedang berjalan |
| **Space = Pause/Play** | Keyboard shortcut untuk menjeda/melanjutkan animasi |

### Panel Grafik (Kanan)

| Fitur | Deskripsi |
|---|---|
| **Kurva Risiko Interaktif** | Line chart Chart.js: risiko (%) vs usia; titik usia terpilih ditandai merah |
| **Pie Chart Distribusi ND** | Doughnut chart proporsi Non-disjunction Meiosis I vs Meiosis II |
| **Hasil Statistik Monte Carlo** | Card: jumlah aneuploid, % risiko observasi, jumlah ND Meiosis I & II |
| **Panel Prediksi Sindrom** | Daftar sindrom yang diprediksi beserta jumlah kejadian dari simulasi |

### --Fitur UX Global

| Fitur | Deskripsi |
|---|---|
| **Loading Overlay** | Animasi spinner dengan pesan kontekstual selama komputasi berjalan |
| **Toast Notification** | Notifikasi kecil muncul di bawah (sukses / error / info) |
| **Responsif** | Layout 3-kolom menyesuaikan ukuran layar |
| **Dark Glassmorphism** | Desain modern: dark mode + blur glass + neon accent cyan/violet |

---

## Gambaran Lo-Fi UI (Wireframe)

Aplikasi dibangun sebagai **Single Page Application (SPA)** dengan tata letak (layout) 3-kolom yang memaksimalkan area kerja visual di tengah, dan menempatkan area kontrol serta analitik di sisi kiri dan kanan.

```text
+---------------------------------------------------------------------------------------------------+
| [🧬 Icon] MeioVis - Chromosome Aneuploidy Predictor             [Simulasi] [Kurva Risiko] [Info]  |
+---------------------------------------------------------------------------------------------------+
|                          |                                                  |                     |
|  ⚙️ PARAMETER SIMULASI   |                                                  |  📉 KURVA RISIKO    |
|  ----------------------  |                                                  |  ---------------    |
|  Usia Maternal: [ 30 ]   |                                                  |  +---------------+  |
|  [=========O---------]   |             (VIEWPORT THREE.JS 3D)               |  |      /    * |  |
|                          |                                                  |  |    /      | |  |
|  Iterasi: [ 10.000 ▼ ]   |                                                  |  |__/        | |  |
|  Fokus:   [ Chr 21 ▼ ]   |             (Sel Induk / Gamet 3D)               |  +---------------+  |
|                          |                                                  |  (Line chart usia)  |
|  [▶ JALANKAN SIMULASI]   |              (Spindle Fibers 3D)                 |                     |
|  [📊 Analisis Semua]     |             (Kromosom 3D Animasi)                |                     |
|                          |                                                  |                     |
|  ----------------------  |                                                  |                     |
|                          |                                                  |  🥧 DISTRIBUSI ND   |
|  🔬 PROFIL RISIKO        |                                                  |  ---------------    |
|  ----------------------  |                                                  |       .--.          |
|     /--------\           |                                                  |      /    \         |
|    /  [ 0.35% ] \        |                                                  |      \    /         |
|   |  Total Risiko|       |                                                  |       '--'          |
|    \____________/        |                                                  |  (Doughnut chart)   |
|                          |                                                  |                     |
|  Meiosis I  : 0.26%      |                                                  |                     |
|  Meiosis II : 0.09%      |                                                  |                     |
|  Kategori   : [RENDAH]   |                                                  |                     |
|  Rasio vs 25: 1.7x       |                                                  |                     |
|                          |                                                  |                     |
|  ----------------------  |                                                  |                     |
|                          |                                                  |                     |
|  📈 HASIL MONTE CARLO    |                                                  |                     |
|  ----------------------  |                                                  |                     |
|  [Aneuploid: 35      ]   |                                                  |                     |
|  [Risiko Obs: 0.35%  ]   |                                                  |                     |
|                          |                                                  |                     |
|  Prediksi Sindrom:       |                                                  |                     |
|  🔴 Trisomi 21: 22       |                                                  |                     |
|  🔴 Trisomi 18: 8        |     [Interfase] [Profase] [Metafase] [Anafase]   |                     |
|                          |                                                  |                     |
+---------------------------------------------------------------------------------------------------+
| Toast Notification / Error Message muncul di sini secara popup                                    |
+---------------------------------------------------------------------------------------------------+
```

### Penjelasan Posisi Fitur
1. **Header (Atas)**: Berisi branding aplikasi dan menu navigasi (berguna untuk scroll/tab di versi mobile).
2. **Left Panel (Control & Stats)**:
   - **Input Section**: Memuat slider interaktif untuk mengatur usia. Tiap kali slider digeser, "Profil Risiko" di bawahnya langsung ter-update. Diakhiri dengan tombol utama `[▶ JALANKAN SIMULASI]`.
   - **Profil Risiko**: Menampilkan risiko teoritis sebelum simulasi berjalan (sebagai referensi cepat). Memiliki Gauge SVG/Canvas setengah lingkaran.
   - **Hasil Simulasi**: Bagian ini akan muncul setelah simulasi Monte Carlo selesai berjalan. Menampilkan jumlah absolut kejadian aneuploid dan rincian sindrom yang dihasilkan.
3. **Center Panel (Visualisasi 3D)**: Merupakan area terluas berisi kanvas WebGL/Three.js. Pengguna dapat melakukan rotasi (drag) dan zoom (scroll) secara bebas. Di bagian paling bawah kanvas, terdapat `Stage Bar` yang berfungsi seperti progress tracker yang akan menyala mengikuti fase meiosis yang sedang berlangsung (Interfase hingga Gamet).
4. **Right Panel (Analitik & Grafik)**:
   - **Kurva Risiko**: Memuat *line chart* (Chart.js) untuk usia 15-50 tahun. Titik merah (asterisk di wireframe) akan bergeser mengikuti input usia di panel kiri.
   - **Distribusi ND**: Memuat *pie/doughnut chart* yang memecah persentase kegagalan kromosom berdasarkan tahap Meiosis I atau Meiosis II.
