"""Satu URL untuk seluruh portofolio.

  /                  halaman portofolio (site/)
  /demo/katering/    aplikasi Flask Dapur Lestari   (apps/katering)
  /demo/stokku/      aplikasi Flask Stokku          (apps/stokku)
  /demo/stocklab/    StockLab (Flask + JS)          (apps/stocklab)  -- butuh numpy/pandas/scikit-learn/plotly

Aplikasi demo dimuat saat server start dan hanya dipanggil bila panelnya diklik.
Data demo direset tiap server start (DEMO_MODE=1). Satu proses saja (jangan pakai banyak worker).

Variabel lingkungan (semua opsional):
  DEMO_ADMIN_PASSWORD / DEMO_KASIR_PASSWORD  sandi demo; bila kosong dibuat acak dan dicetak ke log
  SECRET_KEY    penanda sesi; bila kosong acak tiap start
  DATA_DIR      lokasi file SQLite demo (default: folder sementara)
  TRUST_PROXY=1 percayai header X-Forwarded-* (set di belakang proxy hosting)
  PORT          untuk `python server.py` (default 8000)
"""
import importlib.util
import os
import secrets
import sys
import tempfile
from pathlib import Path

from flask import Flask, send_from_directory
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DATA = Path(os.environ.get("DATA_DIR") or Path(tempfile.gettempdir()) / "portfolio-demo")
DATA.mkdir(parents=True, exist_ok=True)

ADMIN_PW = os.environ.get("DEMO_ADMIN_PASSWORD") or secrets.token_urlsafe(8)
KASIR_PW = os.environ.get("DEMO_KASIR_PASSWORD") or secrets.token_urlsafe(8)
SECRET = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
os.environ["ADMIN_PASSWORD"] = ADMIN_PW  # dibaca kedua aplikasi saat login (saat request), jadi harus tetap terpasang
if not os.environ.get("DEMO_ADMIN_PASSWORD"):
    print(f"[demo] kata sandi admin acak: {ADMIN_PW}  |  kasir: {KASIR_PW}", file=sys.stderr)


def load_demo(name, hint):
    """Muat apps/<name>/app.py sebagai modul terpisah dengan konfigurasi demo, lalu kembalikan objek Flask-nya."""
    env = {
        "DEMO_MODE": "1", "DEMO_KASIR_PASSWORD": KASIR_PW,
        "SECRET_KEY": SECRET + name, "SESSION_COOKIE_NAME": f"sess_{name}",
        "DB_PATH": str(DATA / f"{name}.db"), "DEMO_HINT": hint, "EMBED_DEMO": "0",
    }
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        spec = importlib.util.spec_from_file_location(f"demo_{name}", ROOT / "apps" / name / "app.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod  # perlu agar Flask menemukan folder templates/static
        spec.loader.exec_module(mod)
        return mod.app
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v



def load_stocklab():
    """StockLab butuh pustaka sains data yang berat. Bila tidak terpasang (hosting kecil),
    kembalikan halaman penjelasan alih-alih membuat seluruh situs gagal start."""
    folder = ROOT / "apps" / "stocklab"
    env = {"SESSION_COOKIE_NAME": "sess_stocklab", "STOCKLAB_CACHE_DIR": str(DATA / "stocklab_cache")}
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    sys.path.insert(0, str(folder))
    try:
        from stocklab_web.app import create_app
        return create_app()
    except Exception as error:  # ImportError dari numpy/pandas/sklearn/plotly, dsb.
        print(f"[demo] StockLab tidak dimuat: {type(error).__name__}: {error}", file=sys.stderr)
        sys.path.remove(str(folder))
        fallback = Flask("stocklab_off", static_folder=None)

        @fallback.route("/", defaults={"path": ""})
        @fallback.route("/<path:path>")
        def off(path):
            return ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
                    "<body style='font-family:system-ui;background:#0b0b0f;color:#eee;padding:2rem;max-width:560px;margin:auto'>"
                    "<h2>StockLab tidak aktif di server ini</h2><p>Pustaka sains data (numpy, pandas, scikit-learn, plotly) "
                    "belum terpasang atau server terlalu kecil untuk menjalankannya. Kode dan cara menjalankannya ada di GitHub.</p>"), 503
        return fallback
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


katering = load_demo("katering", f"Kata sandi admin demo: {ADMIN_PW}")
stokku = load_demo("stokku", f"Akun demo: admin / {ADMIN_PW}  ·  kasir / {KASIR_PW}")
stocklab = load_stocklab()

root = Flask("portfolio", static_folder=None)


@root.get("/")
def home():
    return send_from_directory(SITE, "index.html")


@root.get("/healthz")
def healthz():
    return "ok"


@root.get("/<path:path>")
def site_file(path):  # send_from_directory menolak path keluar dari folder site/
    return send_from_directory(SITE, path)


def secure_headers(wsgi):
    """Hanya situs ini sendiri yang boleh membingkai halaman; cegah sniffing tipe konten."""
    def app(environ, start_response):
        def sr(status, headers, exc=None):
            names = {h[0].lower() for h in headers}
            if "x-frame-options" not in names:
                headers.append(("X-Frame-Options", "SAMEORIGIN"))
            headers.append(("X-Content-Type-Options", "nosniff"))
            return start_response(status, headers, exc)
        return wsgi(environ, sr)
    return app


application = secure_headers(DispatcherMiddleware(root, {"/demo/katering": katering, "/demo/stokku": stokku, "/demo/stocklab": stocklab}))
if os.environ.get("TRUST_PROXY") == "1":
    application = ProxyFix(application, x_for=1, x_proto=1, x_host=1)

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple("127.0.0.1", int(os.environ.get("PORT", 8000)), application, threaded=True)
