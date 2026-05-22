## Backend Notes

Bagian backend sekarang memakai gaya penamaan `camelCase` untuk variabel runtime, field model, dan JSON response yang dipakai API.

### Aturan yang dipakai

- Variabel lokal, field dataclass, dan payload API: `camelCase`.
- Nama file CSV di `data/raw/` tetap mengikuti sumber data asal (`snake_case`), tetapi `DatasetLoader` mengubah row menjadi `camelCase` saat dikembalikan ke API.
- Notebook di `backend/notebooks/meiosis_simulation.ipynb` memakai nama variabel `camelCase` yang sama agar selaras dengan backend dan laporan.

### File inti

- [backend/src/api/main.py](backend/src/api/main.py) - FastAPI endpoint dan request model.
- [backend/src/models/risk_model.py](backend/src/models/risk_model.py) - Model risiko maternal age.
- [backend/src/models/gamete.py](backend/src/models/gamete.py) - Model gamet dan prediksi sindrom.
- [backend/src/models/chromosome.py](backend/src/models/chromosome.py) - Model kromosom dan pasangan kromosom.
- [backend/src/simulation/monte_carlo.py](backend/src/simulation/monte_carlo.py) - Simulasi Monte Carlo.
- [backend/src/simulation/statistics.py](backend/src/simulation/statistics.py) - Analisis statistik hasil simulasi.
- [backend/src/data/loader.py](backend/src/data/loader.py) - Loader CSV dan normalisasi key ke `camelCase`.
- [backend/notebooks/meiosis_simulation.ipynb](backend/notebooks/meiosis_simulation.ipynb) - Notebook analisis yang mengikuti nama variabel backend.

### Catatan penggunaan

- Jalankan backend dengan:

```powershell
python -m uvicorn backend.src.api.main:app --reload --port 8000
```

- Endpoint data, risiko, dan simulasi sekarang mengembalikan field `camelCase`.
- Jika frontend masih membaca key lama `snake_case`, perlu disesuaikan ke format baru.
