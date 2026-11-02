/* Daftar proyek. Edit file ini saja untuk menambah/mengubah panel.
   type: "embed"    -> klik membuka penampil dengan website hidup (iframe)
         "redirect" -> klik langsung pindah ke situs proyek (mis. game)
   url:  alamat demo. Kosong ("") = belum ada demo online; panel tetap tampil dengan label "segera".
   hint: info untuk pengunjung (mis. akun demo), tampil di atas penampil. */
const PROJECTS = [
  {
    id: "warung", cat: "web", type: "embed",
    title: "Warung Bu Ningsih", sub: "Website profil kuliner (contoh UMKM)",
    desc: "Menu dengan filter, jam buka dengan status buka/tutup otomatis, tombol pesan WhatsApp.",
    tags: ["HTML", "CSS", "JavaScript"], img: "img/warung.png",
    url: "demos/warung/index.html", repo: ""
  },
  {
    id: "barbershop", cat: "web", type: "embed",
    title: "Pangkas Rapi", sub: "Website profil jasa (contoh UMKM)",
    desc: "Daftar layanan dan harga, testimoni berganti otomatis, booking lewat WhatsApp.",
    tags: ["HTML", "CSS", "JavaScript"], img: "img/barbershop.png",
    url: "demos/barbershop/index.html", repo: ""
  },
  {
    id: "katering", cat: "app", type: "embed",
    title: "Dapur Lestari", sub: "Form pesanan + admin (contoh UMKM)",
    desc: "Pesanan tersimpan di database, admin dengan login, filter status, dan ekspor CSV.",
    tags: ["Python", "Flask", "SQLite"], img: "img/katering.png",
    url: "demo/katering/", // dilayani server.py (satu URL dengan portofolio)
    hint: "Untuk melihat admin, klik \"Admin\" di bagian bawah halaman; kata sandi demo tertera di halaman login.",
    repo: ""
  },
  {
    id: "stokku", cat: "app", type: "embed",
    title: "Stokku", sub: "Kasir + inventori, dua peran (contoh UMKM)",
    desc: "Kasir (POS) dan admin: penjualan otomatis mengurangi stok, laporan, kelola pegawai.",
    tags: ["Python", "Flask", "SQLite"], img: "img/stokku.png",
    url: "demo/stokku/",
    hint: "Akun demo (admin dan kasir) tertera di halaman login. Coba keduanya untuk melihat perbedaan peran.",
    repo: ""
  },
  {
    id: "research", cat: "research", type: "embed",
    title: "Scientific Research", sub: "Technical Whitepapers & Data Forensics",
    desc: "Tiga riset domain nyata dengan sumber resmi: Ekstraksi Laporan Keuangan IDX, Deteksi Kartel Pengadaan LKPP (Benford & Graf), dan Pemantauan Deforestasi Satelit Sentinel-2 (U-Net).",
    tags: ["Whitepaper", "Financial AI", "Forensic Data", "Remote Sensing"], img: "img/research.png",
    url: "research/index.html",
    hint: "Klik kartu mana pun di dalam untuk membaca naskah paper lengkap, formulasi matematis, dan modul kode Python.",
    repo: ""
  },
  {
    id: "ds", cat: "data", type: "embed",
    title: "Data Science Project", sub: "Studi kasus lomba dan kuliah (Python & R)",
    desc: "Tujuh lomba dan lima belas proyek kuliah, dituturkan sebagai riset: masalah, data, pendekatan, temuan, dan peringkat.",
    tags: ["Python", "R", "Machine Learning", "Statistika"], img: "img/ds.png",
    url: "ds/index.html",
    hint: "Klik kartu mana pun untuk membaca studi kasusnya. Dataset tidak dipublikasikan; notebook terbaik ditautkan ke GitHub.",
    repo: "https://github.com/Ezra696969/data-science-lomba"
  },
  {
    id: "stocklab", cat: "data", type: "embed",
    title: "StockLab", sub: "Backtesting saham IDX",
    desc: "Lab backtesting model ML: walk-forward, biaya transaksi, dan pemeriksaan yang berusaha mementahkan hasilnya.",
    tags: ["Python", "Flask", "JavaScript"], img: "img/stocklab.png",
    url: "demo/stocklab/", // StockLab versi Flask/JS, dilayani server.py (satu URL)
    hint: "Tekan Jalankan untuk backtest. Validasi dan Lintas saham melatih ulang model puluhan kali, jadi di hosting gratis bisa memakan beberapa menit.",
    repo: "https://github.com/Ezra696969/stocklab"
  },
  {
    id: "mahjong", cat: "game", type: "redirect",
    title: "Mahjong Online", sub: "Game multiplayer 4 pemain",
    desc: "Main bareng teman lewat browser, kursi kosong diisi bot. Klik untuk membuka game.",
    tags: ["Node.js", "WebSocket"], img: "img/mahjong.png",
    url: "https://ro47kz3rtroi-production-vgphc20e.us-central1.suga.run/", // situs game (redirect)
    repo: "https://github.com/Ezra696969/mahjong-online"
  }
];
const CATS = { all: "Semua", research: "Research", data: "Data & Saham", app: "Aplikasi", web: "Website", game: "Game" };
