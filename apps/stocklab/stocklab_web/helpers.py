"""Fungsi pembantu yang di versi Streamlit hidup di ``stocklab/ui/app.py``.

Isinya disalin tanpa perubahan logika (modul aslinya mengimpor Streamlit di
tingkat atas, jadi tidak bisa diimpor di sini). Pemformat angka disalin dari
``stocklab/ui/components.py``.
"""

from __future__ import annotations

from typing import Any

from stocklab.ui.pipeline import RunConfig
from stocklab.ui.state import TrialLog
from stocklab.llm.context import build_context

PRESET_TICKERS = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK",
    "UNVR.JK", "ICBP.JK", "KLBF.JK", "AAPL", "MSFT",
]

#: Universe awal untuk pemeriksaan lintas saham (sama dengan versi Streamlit).
DEFAULT_UNIVERSE = ["BBCA.JK", "BBRI.JK", "TLKM.JK", "ASII.JK", "AAPL"]


def fmt_pct(value: Any, digits: int = 1) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    return "-" if number != number else f"{number * 100:.{digits}f}%"


def fmt_num(value: Any, digits: int = 2) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    return "-" if number != number else f"{number:.{digits}f}"


def fmt_money(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    return "-" if number != number else f"{number:,.0f}"


def columns_of(feature_config) -> list[str]:
    from stocklab.features import column_names

    return column_names(feature_config)


def window_years(ohlcv) -> int:
    """Panjang jendela stabilitas periode, menyesuaikan data yang tersedia.

    Dipilih jendela terpanjang yang masih menyisakan minimal dua jendela untuk
    dibandingkan; satu jendela tidak mengatakan apa-apa soal stabilitas.
    """
    span_years = (ohlcv.index[-1] - ohlcv.index[0]).days / 365.25
    for candidate in (3, 2):
        if span_years >= candidate + 1:
            return candidate
    return 2


def grid_for(config: RunConfig) -> dict[str, list]:
    """Grid sempit di sekitar pengaturan user (maks. tiga nilai, dua parameter)."""
    from stocklab.models import get_model_entry

    specs = get_model_entry(config.model_name).param_specs()
    grid: dict[str, list] = {}
    for name, spec in specs.items():
        if len(grid) == 2:
            break
        if spec.kind != "int" or not spec.is_bounded:
            continue
        current = int(config.model_params.get(name, spec.default))
        candidates = sorted(
            {
                max(int(spec.low), current // 2),
                current,
                min(int(spec.high), current * 2),
            }
        )
        if len(candidates) > 1:
            grid[name] = candidates
    return grid


def uploaded_factory(data: bytes, filename: str, policy, train_end, features):
    """Bangun factory adapter dari artifact yang diunggah (berkas ditulis ke berkas sementara)."""
    import tempfile
    from pathlib import Path

    from stocklab.models import load_uploaded_model

    suffix = Path(filename).suffix or ".bin"
    handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    handle.write(data)
    handle.close()

    adapter = load_uploaded_model(
        handle.name,
        policy=policy,
        feature_names=features,
        train_end=train_end or None,
    )
    return lambda: adapter


def make_context(result, trials: TrialLog, validation) -> dict:
    if result is None:
        return build_context(trials=trials.summary())

    return build_context(
        metrics={**result.metrics, "equity_ratio": result.equity_ratio},
        model_name=result.spec.label,
        model_params=result.spec.defaults(),
        features=result.feature_names,
        walkforward=result.walkforward_summary(),
        validation=validation.summary() if validation is not None else None,
        trials=trials.summary(),
        period=result.period(),
    )
