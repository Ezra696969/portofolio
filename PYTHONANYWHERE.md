# Deploy ke PythonAnywhere (akun gratis, tanpa kartu)

Yang hidup di sini: portofolio, Warung, Barbershop, Dapur Lestari, Stokku.
**StockLab tidak aktif** (disk gratis 512 MiB dan akses internet keluar dibatasi): panelnya otomatis menampilkan cuplikan dan tautan GitHub. Mahjong tetap redirect ke situsnya sendiri.

## 1. Akun
Daftar akun **Beginner (gratis)** di pythonanywhere.com. Nama pengguna menjadi alamat situs: `https://NAMA.pythonanywhere.com`.

## 2. Ambil kode dan pasang Flask (tab Consoles → Bash)
```bash
git clone https://github.com/Ezra696969/portofolio.git
mkvirtualenv --python=python3.11 portofolio-env
pip install -r portofolio/requirements-pythonanywhere.txt
```
(Gunakan versi Python yang tersedia di akun Anda bila 3.11 tidak ada, dan samakan di langkah 3.)

## 3. Web app (tab Web → Add a new web app)
- Pilih **Manual configuration**, lalu versi Python yang sama dengan virtualenv.
- **Virtualenv:** `/home/NAMA/.virtualenvs/portofolio-env`
- **Source code / working directory:** `/home/NAMA/portofolio`

## 4. File WSGI (link "WSGI configuration file" di tab Web)
Hapus isinya, ganti dengan ini (ubah `NAMA`; kedua sandi sengaja publik, jangan pakai sandi asli):

```python
import os, sys

path = "/home/NAMA/portofolio"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DEMO_ADMIN_PASSWORD"] = "demo-admin-2026"
os.environ["DEMO_KASIR_PASSWORD"] = "demo-kasir-2026"
os.environ["SECRET_KEY"] = "ganti-dengan-teks-acak-panjang"
os.environ["DATA_DIR"] = "/home/NAMA/portofolio-data"
os.environ["TRUST_PROXY"] = "1"

from server import application
```

## 5. Jalankan
Tombol **Reload** di tab Web, lalu buka `https://NAMA.pythonanywhere.com`. Reload juga mereset data demo.

## Catatan
- Akun gratis harus diperpanjang: di tab Web klik **Run until 1 month from today** sebulan sekali, kalau tidak situs mati.
- Satu web app dan satu worker, sesuai kebutuhan situs ini.
- Pembaruan kode: di console `cd portofolio && git pull`, lalu Reload.
