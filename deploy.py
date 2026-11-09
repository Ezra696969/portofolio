"""
deploy.py — Script Otomatisasi Deploy ke PythonAnywhere
Menjalankan git pull pada console PythonAnywhere dan me-reload web app via REST API.
"""

import os
import sys
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Baca .env lokal jika ada
env_path = ROOT / ".env"
config = {}
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()

TOKEN = os.environ.get("PYTHONANYWHERE_API_TOKEN") or config.get("PYTHONANYWHERE_API_TOKEN")
USERNAME = os.environ.get("PYTHONANYWHERE_USERNAME") or config.get("PYTHONANYWHERE_USERNAME") or "Gregy"
DOMAIN = os.environ.get("PYTHONANYWHERE_DOMAIN") or config.get("PYTHONANYWHERE_DOMAIN") or "Gregy.pythonanywhere.com"

if not TOKEN:
    print("[Error] PYTHONANYWHERE_API_TOKEN tidak ditemukan di .env atau environment variables.")
    sys.exit(1)

HEADERS_JSON = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}
HEADERS_AUTH = {
    "Authorization": f"Token {TOKEN}"
}

def get_active_console():
    """Mendapatkan id console bash yang aktif atau membuat console baru jika belum ada."""
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/"
    req = urllib.request.Request(url, headers=HEADERS_AUTH)
    with urllib.request.urlopen(req) as resp:
        consoles = json.loads(resp.read().decode())
        bash_consoles = [c for c in consoles if c.get("executable") == "bash"]
        if bash_consoles:
            return bash_consoles[0]["id"]
    
    # Buat console baru jika tidak ada
    create_req = urllib.request.Request(
        url,
        data=json.dumps({"executable": "bash"}).encode("utf-8"),
        headers=HEADERS_JSON,
        method="POST"
    )
    with urllib.request.urlopen(create_req) as resp:
        new_console = json.loads(resp.read().decode())
        return new_console["id"]

def pull_and_reload():
    print(f"[*] Menghubungi PythonAnywhere untuk akun: {USERNAME} ({DOMAIN})...")
    cid = get_active_console()
    print(f"[*] Menggunakan Console ID: {cid}")

    # Kirim perintah git pull
    send_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{cid}/send_input/"
    cmd_body = json.dumps({"input": "cd ~/portofolio && git pull\n"}).encode("utf-8")
    req = urllib.request.Request(send_url, data=cmd_body, headers=HEADERS_JSON, method="POST")
    with urllib.request.urlopen(req) as resp:
        if resp.status == 200:
            print("[✓] Perintah 'git pull' terkirim ke server.")

    time.sleep(4)

    # Ambil log output konsol
    out_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/consoles/{cid}/get_latest_output/"
    out_req = urllib.request.Request(out_url, headers=HEADERS_AUTH)
    try:
        with urllib.request.urlopen(out_req) as resp:
            data = json.loads(resp.read().decode())
            lines = data.get("output", "").splitlines()
            print("[*] Output server:")
            for l in lines[-10:]:
                print("   ", l)
    except Exception as e:
        print(f"[!] Tidak dapat mengambil log konsol: {e}")

    # Reload web app
    print(f"[*] Me-reload Web App {DOMAIN}...")
    reload_url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
    reload_req = urllib.request.Request(reload_url, data=b"{}", headers=HEADERS_JSON, method="POST")
    with urllib.request.urlopen(reload_req) as resp:
        if resp.status == 200:
            print(f"[✓] SUKSES! Web app {DOMAIN} berhasil di-reload dan live dengan kode terbaru.")
        else:
            print(f"[!] Reload response code: {resp.status}")

if __name__ == "__main__":
    pull_and_reload()
