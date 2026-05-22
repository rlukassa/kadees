Tidak, datanya tidak dicampur secara acak, melainkan mengalir melalui sebuah pipelining data (alur data) dari hulu ke hilir.

Untuk menjawab pertanyaan Anda: CSV adalah penyimpanan lokal (local storage/database) pada backend disk, sedangkan API adalah cara menyajikannya ke frontend/notebook.

Berikut adalah alur data (data pipeline) yang sebenarnya terjadi pada proyek MeioVis:

Mermaid diagram
Penjelasan Alur Tiap Data:
maternal_age_risk.csv (1.000 baris)

Sumber Asli (PDF & Web): Angka probabilitas risiko per usia ibu diambil dari jurnal ilmiah PDF (Hook 1981, Morris 2002, Savva 2010) yang dikompilasi di web UNSW Embryology.
Penyimpanan (CSV): Berkas generator Python (data/generate_datasets.py) membaca angka probabilitas tersebut untuk mensintesis 1.000 data pasien imajiner, lalu menyimpannya secara lokal ke dalam berkas CSV maternal_age_risk.csv.
Penyajian (API): Backend FastAPI membaca berkas CSV lokal tersebut, lalu menyajikannya secara dinamis ke Jupyter notebook/frontend dalam bentuk JSON melalui endpoint /api/data/maternal-age.
syndrome_reference.csv (37 baris)

Sumber Asli (PDF & Web): Kriteria medis dan karyotype diambil dari panduan klinis PDF ACMG (2016) dan database genetik online OMIM.
Penyimpanan (CSV): Data referensi ini disimpan langsung dalam berkas CSV syndrome_reference.csv di server backend.
Penyajian (API): Backend FastAPI membaca berkas CSV referensi ini, lalu menyajikannya dalam format JSON melalui endpoint /api/data/syndromes.
