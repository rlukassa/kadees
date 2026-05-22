# MeioVis 🧬
**Prediksi Kelainan Kromosom (Aneuploidi) akibat Kegagalan Meiosis**
> Tugas Proyek IF3211 Domain-Specific Computation

---

## Prasyarat

| Tools | Versi Minimum |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ |
| pip | terbaru |
| npm | terbaru |

---

## Setup Development

### 1. Clone / Buka Proyek
```bash
# Pastikan berada di direktori proyek
cd kadees/
```

### 2. Backend — Python (FastAPI)

```bash
# Masuk ke folder backend
cd backend

# (Opsional) Buat virtual environment
py -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Jalankan server development (hot-reload aktif)
uvicorn src.api.main:app --reload --port 8000
```

Server berjalan di: **http://localhost:8000**
Dokumentasi API otomatis: **http://localhost:8000/docs**

### 3. Frontend — Vite + Three.js

> Buka terminal baru (backend tetap berjalan)

```bash
cd frontend

# Install dependencies Node.js
npm install

# Jalankan dev server Vite
npm run dev
```

Frontend berjalan di: **http://localhost:5173**

> Vite secara otomatis mem-proxy request `/api/*` ke `http://localhost:8000`
> sesuai konfigurasi `vite.config.js`. Tidak perlu konfigurasi CORS tambahan.

### 4. Generate / Regenerate Dataset CSV

```bash
# Dari root proyek
py data/generate_datasets.py
```

Menghasilkan:
- `data/raw/maternal_age_risk.csv` — 1.000 rekaman prenatal sintetis
- `data/raw/syndrome_reference.csv` — Referensi sindrom kromosom lengkap

### 5. Jupyter Notebook (Analisis & Validasi)

```bash
cd backend
# Pastikan virtual environment aktif
pip install jupyter

jupyter notebook notebooks/meiosis_simulation.ipynb
```

Notebook akan terbuka di browser pada **http://localhost:8888**

### 6. Menjalankan Unit Tests

```bash
# Dari root proyek, pastikan PYTHONPATH diset
cd kadees/
py -m pytest backend/tests/ -v
```

---

## Urutan Startup yang Benar

```
1. py data/generate_datasets.py    ← Generate dataset (sekali saja)
2. cd backend && uvicorn ...       ← Start FastAPI backend
3. cd frontend && npm run dev      ← Start Vite frontend (terminal baru)
4. Buka http://localhost:5173      ← Akses aplikasi
```

---

## Build Production

```bash
# Frontend
cd frontend
npm run build        # Output: frontend/dist/

# Backend
cd backend
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Troubleshooting

| Problem | Solusi |
|---|---|
| `python not found` | Gunakan `py` (Windows Launcher) |
| Port 8000 sudah dipakai | Ganti port: `uvicorn ... --port 8001` dan update `vite.config.js` |
| CORS error di browser | Pastikan backend berjalan di port 8000 |
| `ModuleNotFoundError` | Jalankan `pip install -r requirements.txt` dalam venv aktif |
| Three.js canvas hitam | Coba refresh browser; pastikan WebGL aktif |
