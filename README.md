# Situs Portofolio — Greg Ezra

**Satu aplikasi, satu URL.** Halaman portofolio berisi panel proyek. Proyek baru dimuat **hanya saat panelnya diklik** (iframe dibuat saat itu juga); setelah itu bisa dipakai penuh.

| Alamat | Isi |
|---|---|
| `/` | Portofolio (`site/`) |
| `/demo/katering/` | Dapur Lestari, Flask + SQLite (`apps/katering`) |
| `/demo/stokku/` | Stokku kasir + inventori, Flask + SQLite (`apps/stokku`) |
| `/demo/stocklab/` | StockLab (backtesting saham), Flask + JavaScript (`apps/stocklab`) |
| `/demos/warung/`, `/demos/barbershop/` | Dua website statis |
| `/healthz` | Cek hidup untuk hosting |

Satu proyek butuh runtime sendiri: **Mahjong** (Node.js + WebSocket) dihubungkan lewat `site/projects.js` dengan tipe `redirect` (klik langsung pindah ke situsnya). StockLab sudah ditulis ulang dari Streamlit ke Flask + JavaScript (kode di `E:\Project\STOCKLAB-WEB`), jadi ikut satu URL.

**Catatan StockLab:** butuh numpy, pandas, scipy, scikit-learn, dan plotly (sekitar 400 MB terpasang) serta CPU yang layak. Di laptop biasa backtest ±20 detik, Validasi ±8 menit, Lintas saham ±4 menit; di hosting gratis bisa beberapa kali lebih lama. Bila pustakanya tidak terpasang, server tetap jalan dan panel StockLab menampilkan penjelasan. Di PythonAnywhere gratis (disk 512 MB) StockLab kemungkinan tidak muat; Render gratis (RAM 512 MB) cukup untuk satu pengunjung.

## Jalankan lokal

```powershell
pip install -r requirements.txt
python server.py          # http://127.0.0.1:8000
```

Kata sandi demo dibuat acak dan dicetak di log bila `DEMO_ADMIN_PASSWORD` / `DEMO_KASIR_PASSWORD` tidak diset. Sandi demo juga tampil di halaman login demo (memang disengaja, untuk publik), jadi **pakai sandi khusus demo**.

## Deploy ke SATU hosting gratis
Cukup satu web service Python (WSGI). Pilih salah satu:

- **Render.com:** push folder ini ke repo GitHub → New → Blueprint → pilih repo (`render.yaml` sudah siap). Sandi demo (publik) sudah tertulis di `render.yaml`, tidak ada yang perlu diisi. Paket gratis tertidur saat sepi; kunjungan pertama menunggu ±30 detik.
- **PythonAnywhere (gratis, 1 web app):** upload folder, buat virtualenv dan `pip install -r requirements.txt`, di file WSGI tulis `from wsgi import application`, set variabel lingkungan di tab Web.

Aturan penting: **satu proses saja** (jangan banyak worker), karena data demo direset saat start dan pembatas login ada di memori. Data demo berada di `DATA_DIR` (default folder sementara) dan hilang saat server restart, sesuai maksudnya.

## Mengubah isi
- Panel dan link: edit `site/projects.js` (isi `url` Mahjong setelah hostingnya jadi; kosong = "Demo segera").
- Aplikasi di `apps/` adalah **salinan** dari `E:\Project\UMKM` dan `E:\Project\STOCKLAB-WEB`. Setelah proyek aslinya berubah, jalankan `.\sync_apps.ps1`.

## Keamanan singkat
Hanya folder `site/` yang bisa diunduh (percobaan `/server.py`, `/apps/...`, `/../` dijawab 404). Halaman hanya boleh dibingkai oleh situs ini sendiri (`X-Frame-Options: SAMEORIGIN`). Setiap aplikasi memakai nama cookie sesi sendiri, jadi login Dapur Lestari dan Stokku tidak saling bocor.
