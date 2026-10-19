"""Mengubah hasil StockLab menjadi blok data untuk browser.

Teks, urutan panel, dan angka mengikuti ``stocklab.ui.panels`` baris demi baris;
bedanya hanya keluarannya: bukan elemen Streamlit, melainkan struktur JSON yang
digambar ``static/app.js``. Semua kalimat tetap ditulis di sini (Python), jadi
satu sumber kebenaran untuk redaksi.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from stocklab_web.charts import cross_section_figure, equity_figure, figure_json
from stocklab_web.helpers import fmt_money, fmt_num, fmt_pct


def cell(value: Any) -> Any:
    """Nilai sel tabel yang aman untuk JSON."""
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp,)):
        return str(value.date()) if value == value else None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return None if math.isnan(number) or math.isinf(number) else number
    return str(value)


def table_block(df: pd.DataFrame, height: int | None = None) -> dict[str, Any]:
    rows = [[cell(index)] + [cell(v) for v in row] for index, row in zip(df.index, df.itertuples(index=False))]
    return {
        "type": "table",
        "index_name": str(df.index.name) if df.index.name else "",
        "columns": [str(c) for c in df.columns],
        "rows": rows,
        "height": height,
    }


def metrics_block(items, accent: str | None = None) -> dict[str, Any]:
    return {
        "type": "metrics",
        "accent": accent,
        "items": [{"label": label, "value": value, "sub": sub} for label, value, sub in items],
    }


# ---------------------------------------------------------------------------
# Kiri atas: equity curve
# ---------------------------------------------------------------------------


def chart_payload(result) -> dict[str, Any] | None:
    if result is None:
        return None

    period = result.period()
    summary = result.walkforward_summary()
    note = (
        f"{period['start']} sampai {period['end']} · {period['n_bars']} bar · "
        f"biaya {period['cost_bps']:.0f} bps · dilatih ulang "
        f"{summary['n_fitted']}x"
    )
    if result.skipped:
        note += (
            f" · {result.skipped} bar awal tidak dihitung karena model "
            f"belum boleh berpendapat"
        )

    metrics = result.metrics
    return {
        "note": note,
        "figure": figure_json(equity_figure(result)),
        "metrics": metrics_block(
            [
                (
                    "Ekuitas Akhir",
                    fmt_money(result.backtest.equity.iloc[-1]),
                    f"pasif {fmt_money(result.backtest.benchmark_equity.iloc[-1])}",
                ),
                ("Sharpe", fmt_num(metrics["sharpe"]), f"pasif {fmt_num(metrics['benchmark_sharpe'])}"),
                (
                    "Drawdown",
                    fmt_pct(metrics["max_drawdown"]),
                    f"pasif {fmt_pct(metrics['benchmark_max_drawdown'])}",
                ),
                ("Eksposur", fmt_pct(metrics["exposure"], 0), f"turnover {fmt_num(metrics['turnover_per_year'], 0)}x/th"),
                ("Biaya", fmt_money(metrics["total_cost"]), f"beta {fmt_num(metrics['beta'])}"),
            ],
            accent="Ekuitas Akhir",
        ),
    }


# ---------------------------------------------------------------------------
# Validasi
# ---------------------------------------------------------------------------


def validation_payload(report, trial_count: int) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "note": f"{trial_count} konfigurasi berbeda dicoba di sesi ini" if trial_count > 1 else None,
        "empty": (
            "Belum dijalankan. Pemeriksaan ini melatih ulang model puluhan kali, "
            "jadi butuh waktu lebih lama daripada satu backtest biasa."
        ),
    }
    if report is None:
        payload["report"] = None
        return payload

    rotation = report.rotation
    costs = report.costs

    if rotation is None:
        rotasi = [{"type": "caption", "text": "Tidak dijalankan."}]
    else:
        rotasi = [
            {
                "type": "md",
                "text": (
                    "Sinyal digeser waktunya ratusan kali. Eksposur dan turnover "
                    "tetap sama, tapi keselarasan dengan harga hancur — jadi yang "
                    "tersisa cuma bentuk posisi tanpa timing."
                ),
            },
            metrics_block(
                [
                    ("Sharpe Asli", fmt_num(rotation.observed), None),
                    ("Acak Tertinggi", fmt_num(rotation.null_max), f"dari {rotation.n_rotations} geseran"),
                    ("p-value", f"{rotation.p_value:.4f}", "makin kecil makin meyakinkan"),
                ],
                accent="Sharpe Asli",
            ),
        ]

    if costs is None:
        biaya = [{"type": "caption", "text": "Tidak dijalankan."}]
    else:
        breakeven = costs.breakeven_bps
        biaya = [
            {
                "type": "md",
                "text": (
                    f"Titik impas **{breakeven:.1f} bps** per sisi transaksi."
                    if breakeven is not None
                    else "Strategi tidak pernah mengungguli pasif pada tingkat biaya mana pun."
                ),
            },
            table_block(
                costs.table[["sharpe", "equity_ratio", "total_cost"]].rename(
                    columns={
                        "sharpe": "Sharpe",
                        "equity_ratio": "Rasio vs Pasif",
                        "total_cost": "Total Biaya",
                    }
                )
            ),
        ]

    parameter = _stability_blocks(
        report.parameters,
        "Model dilatih ulang untuk tiap kombinasi parameter. Hasil yang "
        "runtuh begitu satu slider digeser adalah tanda model menghafal.",
    )
    periode = _stability_blocks(
        report.periods,
        "Alur yang sama dijalankan pada beberapa rentang waktu. Ini yang "
        "paling sering mementahkan strategi yang lolos pemeriksaan lain.",
        skipped_reason=(
            "Rentang tanggalnya terlalu pendek untuk dibagi menjadi "
            "beberapa jendela yang bisa dibandingkan. Perpanjang rentang "
            "di panel kiri — minimal tiga tahun — lalu jalankan ulang."
        ),
    )

    deflated = None
    if report.deflated_sharpe == report.deflated_sharpe:
        deflated = {"value": float(report.deflated_sharpe), "n": int(report.n_trials_counted)}

    payload["report"] = {
        "concerns": {
            "type": "concerns",
            "items": list(report.concerns),
            "empty": (
                "Pemeriksaan yang dijalankan tidak menemukan masalah yang dicarinya. "
                "Itu bukan berarti strategi ini bagus."
            ),
        },
        "tabs": [
            {"label": "Rotasi", "blocks": rotasi},
            {"label": "Biaya", "blocks": biaya},
            {"label": "Parameter", "blocks": parameter},
            {"label": "Periode", "blocks": periode},
        ],
        "deflated": deflated,
    }
    return payload


def _stability_blocks(report, explanation: str, skipped_reason: str | None = None) -> list[dict[str, Any]]:
    """Pemeriksaan yang dilewati harus menyebutkan alasannya (lihat versi Streamlit)."""
    if report is None:
        return [{"type": "caption", "text": skipped_reason or "Tidak dijalankan pada run ini."}]

    spread = report.sharpe_spread()
    return [
        {"type": "md", "text": explanation},
        metrics_block(
            [
                ("Run", str(report.n_runs), f"{report.n_failed} gagal" if report.n_failed else None),
                ("Sharpe Terburuk", fmt_num(spread["min"]), f"median {fmt_num(spread['median'])}"),
                ("Unggul Nominal", fmt_pct(report.win_rate, 0), None),
                ("Unggul Sharpe", fmt_pct(report.sharpe_win_rate, 0), None),
            ],
            accent="Sharpe Terburuk",
        ),
        table_block(report.table, height=210),
    ]


# ---------------------------------------------------------------------------
# Lintas saham
# ---------------------------------------------------------------------------


def cross_payload(report) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "empty": (
            "Belum dijalankan. Pemeriksaan ini mengulang seluruh alur untuk "
            "tiap aset, jadi paling lama di antara semuanya — tapi juga yang "
            "paling sering membantah hasil yang lolos pemeriksaan lain."
        ),
    }
    if report is None:
        payload["report"] = None
        return payload

    summary = report.summary()
    payload["report"] = {
        "concerns": {
            "type": "concerns",
            "items": list(report.concerns()),
            "empty": (
                "Metode ini bertahan di sebagian besar aset yang diuji. Itu bukan "
                "jaminan, hanya berarti hasilnya tidak bergantung pada satu saham."
            ),
        },
        "metrics": metrics_block(
            [
                (
                    "Unggul Sharpe",
                    fmt_pct(summary["sharpe_win_rate"], 0),
                    f"nominal {fmt_pct(summary['win_rate'], 0)}",
                ),
                (
                    "Sharpe Median",
                    fmt_num(summary["median_sharpe"]),
                    f"terburuk {fmt_num(summary['worst_sharpe'])}",
                ),
                (
                    "Aset",
                    f"{summary['n_assets']:.0f}",
                    f"{summary['n_failed']:.0f} gagal" if summary["n_failed"] else None,
                ),
                (
                    "Pengamatan Bebas",
                    fmt_num(summary["effective_sample_size"], 1),
                    f"korelasi {fmt_num(summary['mean_correlation'])}",
                ),
            ],
            accent="Unggul Sharpe",
        ),
        "figure": figure_json(cross_section_figure(report)),
        "table": table_block(report.table),
    }
    return payload
