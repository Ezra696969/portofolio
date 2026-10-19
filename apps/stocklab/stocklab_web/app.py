"""StockLab versi Flask + JavaScript.

Antarmuka identik dengan versi Streamlit (``stocklab/ui``), tetapi tidak
membutuhkan Streamlit: mesin perhitungan (paket ``stocklab``) dipakai apa
adanya, dan logika alur (``stocklab.ui.pipeline``, ``stocklab.ui.state``) juga
tidak diubah.

Peta sederhana:

* ``GET  /``                  halaman aplikasi
* ``GET  /api/meta``          katalog model, indikator, preset, nilai awal kontrol
* ``GET  /api/state``         keadaan sesi pengunjung (hasil, validasi, chat, ...)
* ``POST /api/run|validate|cross|chat``   memulai pekerjaan di latar belakang
* ``GET  /api/job``           kemajuan pekerjaan (di-poll browser)
* ``POST /api/reset_trials``  tombol "Reset hitungan"

Keadaan tiap pengunjung (``st.session_state`` di versi lama) disimpan di server,
dikunci oleh cookie sesi, dan dibatasi jumlahnya.
"""

from __future__ import annotations

import io
import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from flask import Flask, abort, jsonify, make_response, render_template, request

from stocklab.data import DEFAULT_END, DEFAULT_START, load_csv, load_ohlcv
from stocklab.data.loader import _cache_path, normalize_ohlcv
from stocklab.features import FEATURES, FeatureConfig
from stocklab.llm.client import ChatClient
from stocklab.models import LoadPolicy, catalog
from stocklab.ui.pipeline import RunConfig, make_experiment, run_pipeline
from stocklab.ui.state import Trial, TrialLog
from stocklab.validation import cross_section, validate

from stocklab_web import helpers
from stocklab_web.helpers import DEFAULT_UNIVERSE, PRESET_TICKERS
from stocklab_web.views import chart_payload, cross_payload, validation_payload

ROOT = Path(__file__).resolve().parent.parent
SHIPPED_CACHE = ROOT / "cache"  # data harga bawaan (rentang default), hanya dibaca
MAX_SESSIONS = int(os.environ.get("STOCKLAB_MAX_SESSIONS", 40))
SESSION_TTL = 3 * 3600
MAX_JOBS = int(os.environ.get("STOCKLAB_MAX_JOBS", 2))  # pekerjaan berat bersamaan, sisanya antre
MAX_UPLOAD = 64 * 1024 * 1024
#: Pickle/joblib menjalankan kode dari berkas yang diunggah. Di server publik ini
#: dimatikan; nyalakan hanya di mesin sendiri dengan STOCKLAB_ALLOW_PICKLE=1.
ALLOW_PICKLE = os.environ.get("STOCKLAB_ALLOW_PICKLE") == "1"


# ---------------------------------------------------------------------------
# Sesi & pekerjaan
# ---------------------------------------------------------------------------


@dataclass
class Job:
    id: str
    kind: str
    status: str = "queued"  # queued | running | done | error
    message: str = "Menunggu giliran..."
    progress: float | None = None
    error: str | None = None


@dataclass
class Session:
    sid: str
    lock: threading.RLock = field(default_factory=threading.RLock)
    trials: TrialLog = field(default_factory=TrialLog)
    messages: list[dict[str, str]] = field(default_factory=list)
    result: Any = None
    validation: Any = None
    cross_section: Any = None
    chat_client: ChatClient | None = None
    job: Job | None = None
    seen: float = field(default_factory=time.time)

    def busy(self) -> bool:
        return self.job is not None and self.job.status in ("queued", "running")


class Store:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def get(self, sid: str | None) -> tuple[Session, bool]:
        with self._lock:
            now = time.time()
            for key in [k for k, s in self._sessions.items() if now - s.seen > SESSION_TTL and not s.busy()]:
                del self._sessions[key]
            session = self._sessions.get(sid or "")
            created = session is None
            if created:
                while len(self._sessions) >= MAX_SESSIONS:
                    oldest = min(self._sessions.values(), key=lambda s: s.seen)
                    del self._sessions[oldest.sid]
                session = Session(sid=secrets.token_urlsafe(24))
                self._sessions[session.sid] = session
            session.seen = now
            return session, created


STORE = Store()
SLOTS = threading.BoundedSemaphore(MAX_JOBS)


def start_job(session: Session, kind: str, work) -> Job:
    """Jalankan ``work(job)`` di thread; hanya satu pekerjaan per pengunjung."""
    with session.lock:
        if session.busy():
            abort(409, "Masih ada proses yang berjalan.")
        job = Job(id=secrets.token_hex(6), kind=kind)
        session.job = job

    def runner() -> None:
        try:
            with SLOTS:
                job.status = "running"
                job.message = {"run": "Memuat data...", "validate": "Menjalankan pemeriksaan — model dilatih ulang puluhan kali...",
                               "cross": "Menyiapkan...", "chat": "Menyusun jawaban..."}.get(kind, "Memproses...")
                work(job)
            job.status = "done"
        except Exception as error:  # ditampilkan apa adanya, seperti st.error di versi lama
            job.error = f"{type(error).__name__}: {error}"
            job.status = "error"

    threading.Thread(target=runner, daemon=True).start()
    return job


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

_PRICE_CACHE: dict[tuple, pd.DataFrame] = {}
_PRICE_LOCK = threading.Lock()


def load_ticker(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Setara ``@st.cache_data _load_ticker``; membaca data bawaan lebih dulu."""
    key = (ticker, start, end)
    with _PRICE_LOCK:
        if key in _PRICE_CACHE:
            return _PRICE_CACHE[key]
    shipped = _cache_path(SHIPPED_CACHE, ticker, start, end)
    if shipped.exists():
        frame = normalize_ohlcv(pd.read_parquet(shipped))
    else:
        writable = Path(os.environ.get("STOCKLAB_CACHE_DIR") or ROOT / "cache_runtime")
        frame = load_ohlcv(ticker, start, end, cache_dir=writable)
    with _PRICE_LOCK:
        if len(_PRICE_CACHE) >= 64:
            _PRICE_CACHE.pop(next(iter(_PRICE_CACHE)))
        _PRICE_CACHE[key] = frame
    return frame


def load_data(settings: dict, csv_bytes: bytes | None) -> pd.DataFrame:
    start, end = settings["start"], settings["end"]
    if settings["source"] == "Berkas CSV":
        if csv_bytes is None:
            raise ValueError("unggah berkas CSV dulu, atau pilih sumber Ticker")
        return load_csv(io.BytesIO(csv_bytes)).loc[start:end]
    return load_ticker(settings["ticker"], start, end)


# ---------------------------------------------------------------------------
# Pembacaan masukan (batas sama dengan kontrol di versi Streamlit)
# ---------------------------------------------------------------------------


def _num(raw: Any, low: float, high: float, default: float, integer: bool = False):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = default
    value = min(max(value, low), high)
    return int(round(value)) if integer else value


def coerce_params(specs, given: dict) -> dict[str, Any]:
    """Nilai kontrol -> parameter, memakai ParamSpec masing-masing (opaque dilewati)."""
    values: dict[str, Any] = {}
    for name, spec in specs.items():
        if not spec.is_editable:
            continue
        raw = given.get(name, spec.default)
        try:
            if spec.kind == "bool":
                values[name] = bool(raw)
            elif spec.kind == "choice" and spec.choices:
                values[name] = raw if raw in list(spec.choices) else spec.default
            elif spec.kind in ("int", "float"):
                values[name] = spec.clamp(raw) if spec.is_bounded else (int(raw) if spec.kind == "int" else float(raw))
            else:
                values[name] = raw
        except (TypeError, ValueError):
            values[name] = spec.default
    return values


def parse_settings(raw: dict) -> dict:
    entries = catalog()
    source = raw.get("source", "Ticker")
    if source not in ("Ticker", "Berkas CSV"):
        abort(400, "Sumber data tidak dikenal.")
    ticker = raw.get("ticker")
    if source == "Ticker" and ticker not in PRESET_TICKERS:
        abort(400, "Simbol tidak ada di daftar.")
    try:
        start = date.fromisoformat(str(raw.get("start") or DEFAULT_START))
        end = date.fromisoformat(str(raw.get("end") or DEFAULT_END))
    except ValueError:
        abort(400, "Tanggal tidak valid.")

    run = raw.get("run") or {}
    horizon = _num(run.get("horizon"), 1, 10, 1, True)
    settings = {
        "source": source,
        "ticker": ticker,
        "start": str(start),
        "end": str(end),
        "universe": [t for t in (raw.get("universe") or []) if t in PRESET_TICKERS],
        "run": {
            "initial_capital": float(_num(run.get("initial_capital"), 1_000, 10_000_000_000, 100_000)),
            "cost_bps": float(_num(run.get("cost_bps"), 0, 60, 10)),
            "slippage_bps": float(_num(run.get("slippage_bps"), 0, 30, 5)),
            "train_size": _num(run.get("train_size"), 60, 756, 252, True),
            "test_size": _num(run.get("test_size"), 5, 126, 21, True),
            "expanding": bool(run.get("expanding", True)),
            "horizon": horizon,
        },
    }

    model = raw.get("model") or {}
    name = model.get("name")
    if name not in entries:
        abort(400, "Model tidak dikenal.")
    sizing = model.get("sizing", "binary")
    if sizing not in ("binary", "scaled"):
        abort(400, "Ukuran posisi tidak dikenal.")
    features = []
    for item in raw.get("features") or []:
        fname = (item or {}).get("name")
        if fname not in FEATURES:
            abort(400, f"Indikator tidak dikenal: {fname}")
        features.append(FeatureConfig(fname, coerce_params(FEATURES[fname].params, item.get("params") or {})))

    settings["features"] = tuple(features)
    settings["model_name"] = name
    settings["model_params"] = coerce_params(entries[name].param_specs(), model.get("params") or {})
    settings["threshold"] = float(_num(model.get("threshold"), 0.5, 0.8, 0.5))
    settings["sizing"] = sizing
    upload = raw.get("upload") or {}
    settings["allow_pickle"] = bool(upload.get("allow_pickle"))
    settings["train_end"] = upload.get("train_end") or None
    return settings


def make_config(settings: dict) -> RunConfig:
    return RunConfig(
        features=settings["features"],
        model_name=settings["model_name"],
        model_params=settings["model_params"],
        threshold=settings["threshold"],
        sizing=settings["sizing"],
        **settings["run"],
    )


# ---------------------------------------------------------------------------
# Aplikasi Flask
# ---------------------------------------------------------------------------


def param_json(spec) -> dict[str, Any]:
    return {
        "name": spec.name,
        "kind": spec.kind,
        "default": spec.default,
        "low": spec.low,
        "high": spec.high,
        "step": spec.step,
        "choices": list(spec.choices) if spec.choices else None,
        "label": spec.display_label,
        "help": spec.help,
        "editable": spec.is_editable,
        "bounded": spec.is_bounded,
    }


def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(ROOT / "templates"), static_folder=str(ROOT / "static"))
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD + 5 * 1024 * 1024
    cookie = os.environ.get("SESSION_COOKIE_NAME", "sl_sid")

    def session_of() -> Session:
        session, created = STORE.get(request.cookies.get(cookie))
        request.environ["stocklab.new_session"] = session.sid if created else None
        return session

    @app.after_request
    def set_cookie(response):
        sid = request.environ.get("stocklab.new_session")
        if sid:
            response.set_cookie(cookie, sid, httponly=True, samesite="Lax", path=request.script_root or "/")
        response.headers["Cache-Control"] = "no-store" if request.path.startswith(request.script_root + "/api") else response.headers.get("Cache-Control", "")
        return response

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/meta")
    def meta():
        entries = catalog()
        return jsonify({
            "presets": PRESET_TICKERS,
            "default_universe": [t for t in DEFAULT_UNIVERSE if t in PRESET_TICKERS],
            "default_start": DEFAULT_START,
            "default_end": DEFAULT_END,
            "models": [
                {"name": e.name, "label": e.label, "description": e.description, "kind": e.kind,
                 "params": [param_json(s) for s in e.param_specs().values()]}
                for e in entries.values()
            ],
            "default_model": "random_forest" if "random_forest" in entries else next(iter(entries)),
            "features": [
                {"name": n, "label": FEATURES[n].label, "description": FEATURES[n].description,
                 "params": [param_json(s) for s in FEATURES[n].params.values()]}
                for n in sorted(FEATURES)
            ],
            "default_features": [n for n in ("rsi", "roc", "macd") if n in FEATURES],
            "pickle_risk_off": LoadPolicy(allow_pickle=False).describe_risk(),
            "pickle_risk_on": LoadPolicy(allow_pickle=True).describe_risk(),
            "pickle_allowed": ALLOW_PICKLE,
        })

    def chat_client(session: Session) -> ChatClient:
        if session.chat_client is None:
            session.chat_client = ChatClient()
        return session.chat_client

    @app.get("/api/state")
    def state():
        session = session_of()
        with session.lock:
            client = chat_client(session)
            context = helpers.make_context(session.result, session.trials, session.validation)
            job = session.job
            return jsonify({
                "trials": {"n_runs": len(session.trials), "n_distinct": session.trials.n_distinct},
                "chart": chart_payload(session.result),
                "chat": {
                    "note": client.status.explain() if not client.available else None,
                    "greeting": client.greeting(context),
                    "messages": list(session.messages),
                },
                "validation": validation_payload(session.validation, session.trials.n_distinct),
                "cross": cross_payload(session.cross_section),
                "has_result": session.result is not None,
                "job": _job_json(job),
            })

    def _job_json(job: Job | None):
        if job is None:
            return None
        return {"id": job.id, "kind": job.kind, "status": job.status, "message": job.message,
                "progress": job.progress, "error": job.error}

    @app.get("/api/job")
    def job_status():
        session = session_of()
        return jsonify(_job_json(session.job))

    def read_settings() -> dict:
        import json

        payload = request.form.get("settings") if request.form else None
        if payload is None:
            payload = request.get_data(as_text=True) or "{}"
        try:
            return parse_settings(json.loads(payload))
        except json.JSONDecodeError:
            abort(400, "Permintaan tidak valid.")

    @app.post("/api/run")
    def run():
        session = session_of()
        settings = read_settings()
        csv_file = request.files.get("csv")
        csv_bytes = csv_file.read() if csv_file and csv_file.filename else None
        model_file = request.files.get("model_file")
        model_bytes = model_file.read() if model_file and model_file.filename else None
        model_name_file = model_file.filename if model_file else ""

        if model_bytes is not None and settings["allow_pickle"] and not ALLOW_PICKLE:
            abort(400, "Format pickle/joblib dimatikan di server publik ini karena menjalankan kode dari berkas "
                       "yang diunggah. Gunakan ONNX, atau jalankan StockLab di mesin sendiri.")

        def work(job: Job) -> None:
            config = make_config(settings)
            ohlcv = load_data(settings, csv_bytes)
            factory = None
            if model_bytes is not None:
                job.message = "Memeriksa artifact..."
                names = [c for fc in config.features for c in helpers.columns_of(fc)]
                policy = LoadPolicy(allow_pickle=settings["allow_pickle"] and ALLOW_PICKLE)
                factory = helpers.uploaded_factory(model_bytes, model_name_file, policy, settings["train_end"], names)
            job.message = "Menjalankan model..."
            result = run_pipeline(ohlcv, config, factory)
            with session.lock:
                session.result = result
                session.validation = None  # validasi lama menjelaskan run lama
                session.trials.record(Trial(
                    model=config.model_name,
                    params=dict(config.model_params),
                    features=result.feature_names,
                    sharpe=result.metrics["sharpe"],
                    equity_ratio=result.equity_ratio,
                ))

        return jsonify(_job_json(start_job(session, "run", work)))

    @app.post("/api/validate")
    def validate_route():
        session = session_of()
        settings = read_settings()
        csv_file = request.files.get("csv")
        csv_bytes = csv_file.read() if csv_file and csv_file.filename else None
        if session.result is None:
            abort(400, "Jalankan backtest dulu.")

        def work(job: Job) -> None:
            config = make_config(settings)
            ohlcv = load_data(settings, csv_bytes)
            report = validate(
                make_experiment(ohlcv, config),
                grid=helpers.grid_for(config),
                n_rotations=300,
                window_years=helpers.window_years(ohlcv),
            )
            with session.lock:
                session.validation = report

        return jsonify(_job_json(start_job(session, "validate", work)))

    @app.post("/api/cross")
    def cross_route():
        session = session_of()
        settings = read_settings()
        if session.result is None:
            abort(400, "Jalankan backtest dulu.")
        assets = list(settings["universe"])
        if len(assets) < 2:
            abort(400, "Butuh minimal dua aset; pilih di panel kiri.")

        def work(job: Job) -> None:
            config = make_config(settings)
            start, end = settings["start"], settings["end"]

            def build(asset: str):
                return make_experiment(load_ticker(asset, start, end), config)

            def advance(position: int, total: int, asset: str) -> None:
                job.progress = position / total
                job.message = f"{asset} ({position + 1}/{total})"

            job.progress = 0.0
            report = cross_section(build, assets, progress=advance)
            with session.lock:
                session.cross_section = report

        return jsonify(_job_json(start_job(session, "cross", work)))

    @app.post("/api/chat")
    def chat():
        session = session_of()
        data = request.get_json(silent=True) or {}
        question = str(data.get("question") or "").strip()
        if not question:
            abort(400, "Pertanyaan kosong.")
        question = question[:2000]

        def work(job: Job) -> None:
            with session.lock:
                client = chat_client(session)
                context = helpers.make_context(session.result, session.trials, session.validation)
                session.messages.append({"role": "user", "content": question})
                history = session.messages[:-1][-6:]
            reply = client.reply(question, context, history=history)
            with session.lock:
                session.messages.append({"role": "assistant", "content": reply})

        return jsonify(_job_json(start_job(session, "chat", work)))

    @app.post("/api/reset_trials")
    def reset_trials():
        session = session_of()
        with session.lock:
            session.trials.clear()
        return jsonify({"ok": True})

    @app.errorhandler(400)
    @app.errorhandler(409)
    @app.errorhandler(413)
    def _error(error):
        return jsonify({"error": getattr(error, "description", str(error))}), error.code

    return app
