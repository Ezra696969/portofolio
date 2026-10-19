# Situs Portofolio — Greg Ezra

Situs statis (HTML/CSS/JS, tanpa build). Klik panel proyek → website proyek tampil langsung di penampil (iframe) dan bisa dipakai penuh. Game (mahjong) memakai redirect ke situsnya.

## Lihat lokal

```powershell
python -m http.server 8110 --directory E:\Project\PORTFOLIO
```

Buka http://127.0.0.1:8110. Tautan langsung ke satu proyek: `...#warung`, `...#stokku`, dst.

## Menambah / mengubah proyek
Edit **`projects.js`** saja. Isi `url` setelah demo online tersedia; kosong = panel menampilkan "Demo segera".

| Proyek | Yang perlu diisi di `url` |
|---|---|
| warung, barbershop | Sudah jalan (statis, ada di `demos/`). |
| katering, stokku | Alamat Flask yang sudah di-deploy (PythonAnywhere/Render). Jalankan dengan `DEMO_MODE=1` dan `EMBED_DEMO=1` (lihat di bawah; `render.yaml` sudah menyiapkan). |
| stocklab | Alamat Streamlit Cloud + `?embed=true`. |
| mahjong | Alamat game (Render/Hugging Face). Tipe `redirect`: klik langsung pindah. |

## Syarat agar Flask jalan di dalam iframe
Portofolio dan aplikasi berbeda situs, jadi cookie sesi harus `SameSite=None; Secure` (butuh HTTPS). Di server aplikasi set variabel lingkungan `EMBED_DEMO=1` (juga `ADMIN_PASSWORD` dan `SECRET_KEY`). Safari dan mode penyamaran sering memblokir cookie pihak ketiga; karena itu tombol **Buka di tab baru** selalu tersedia sebagai cadangan.

## Deploy (GitHub Pages)
1. Buat repo `Ezra696969.github.io` (atau repo apa saja lalu aktifkan Pages).
2. Push isi folder ini, Settings → Pages → Deploy from branch `main`.
3. Situs hidup di `https://ezra696969.github.io/`.

`demos/warung` dan `demos/barbershop` adalah salinan dari `E:\Project\UMKM`. Kalau proyek aslinya diubah, salin ulang.
