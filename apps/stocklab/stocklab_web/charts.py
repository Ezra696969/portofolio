"""Grafik StockLab: salinan persis dari ``stocklab.ui.panels`` dan ``stocklab.ui.theme``.

Bagian chart saja yang dipindahkan; tidak ada yang bergantung pada Streamlit.
Figure dibangun dengan plotly Python seperti di versi Streamlit, lalu diubah ke
dict biasa untuk dikirim ke plotly.js di browser, sehingga tampilannya identik.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from stocklab.ui.pipeline import RunResult

PALETTE = {
    "strategy": "#FF9F0A",
    "strategy_soft": "rgba(255, 159, 10, 0.16)",
    "passive": "#F5F5F7",
    "passive_soft": "rgba(245, 245, 247, 0.10)",
    "good": "#30D158",
    "warning": "#FFD60A",
    "critical": "#FF453A",
    "ink": "rgba(255, 255, 255, 0.92)",
    "ink_muted": "rgba(255, 255, 255, 0.58)",
    "ink_faint": "rgba(255, 255, 255, 0.34)",
    "grid": "rgba(255, 255, 255, 0.07)",
}


def plotly_layout(height: int = 430) -> dict:
    """Layout plotly yang menyatu dengan panel kaca (latar transparan)."""
    return {
        "height": height,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif',
            "color": PALETTE["ink_muted"],
            "size": 12,
        },
        "margin": {"l": 8, "r": 76, "t": 10, "b": 8},
        "hovermode": "x unified",
        "hoverlabel": {
            "bgcolor": "rgba(28,28,34,0.94)",
            "bordercolor": "rgba(255,255,255,0.16)",
            "font": {"color": PALETTE["ink"], "size": 12},
        },
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "x": 0,
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": PALETTE["ink_muted"], "size": 11},
        },
        "xaxis": {
            "automargin": True,  # bawaan template plotly yang dibuang di figure_json
            "showgrid": False,
            "zeroline": False,
            "linecolor": PALETTE["grid"],
            "tickfont": {"color": PALETTE["ink_faint"], "size": 11},
        },
        "yaxis": {
            "automargin": True,
            "gridcolor": PALETTE["grid"],
            "zeroline": False,
            "linecolor": "rgba(0,0,0,0)",
            "tickfont": {"color": PALETTE["ink_faint"], "size": 11},
        },
    }


def equity_figure(result: RunResult) -> go.Figure:
    equity = result.backtest.equity
    passive = result.backtest.benchmark_equity

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=passive.index,
            y=passive.to_numpy(),
            name="Pasif",
            mode="lines",
            line={"color": PALETTE["passive"], "width": 2, "dash": "dot"},
            hovertemplate="Pasif %{y:,.0f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=equity.index,
            y=equity.to_numpy(),
            name="Strategi",
            mode="lines",
            line={"color": PALETTE["strategy"], "width": 2},
            hovertemplate="Strategi %{y:,.0f}<extra></extra>",
        )
    )

    layout = plotly_layout(height=372)
    # Sumbu dikunci ke rentang data, bukan ke nol (lihat versi Streamlit).
    low = min(float(equity.min()), float(passive.min()))
    high = max(float(equity.max()), float(passive.max()))
    padding = (high - low) * 0.08 or high * 0.02
    layout["yaxis"] = {**layout["yaxis"], "range": [low - padding, high + padding]}
    layout["annotations"] = [
        _end_label(equity, "Strategi", PALETTE["strategy"]),
        _end_label(passive, "Pasif", PALETTE["passive"]),
    ]
    figure.update_layout(**layout)
    figure.update_yaxes(tickformat=",.0f")
    return figure


def _end_label(series: pd.Series, text: str, color: str) -> dict[str, Any]:
    return {
        "x": series.index[-1],
        "y": float(series.iloc[-1]),
        "text": f"  {text}",
        "showarrow": False,
        "xanchor": "left",
        "font": {"color": color, "size": 11},
    }


def cross_section_figure(report) -> go.Figure:
    """Sharpe tiap aset, dengan pasif sebagai penanda pembanding."""
    table = report.table.dropna(subset=["sharpe"]).sort_values("sharpe")

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=table["sharpe"],
            y=table.index,
            orientation="h",
            name="Strategi",
            marker={"color": PALETTE["strategy"]},
            hovertemplate="%{y} · strategi %{x:.2f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=table["benchmark_sharpe"],
            y=table.index,
            mode="markers",
            name="Pasif",
            marker={"color": PALETTE["passive"], "size": 9,
                    "line": {"color": "#0B0B0F", "width": 1.5}},
            hovertemplate="%{y} · pasif %{x:.2f}<extra></extra>",
        )
    )

    layout = plotly_layout(height=max(240, 34 * len(table)))
    layout["margin"] = {"l": 8, "r": 20, "t": 10, "b": 8}
    layout["xaxis"] = {**layout["xaxis"], "title": {"text": "Sharpe"},
                       "zeroline": True, "zerolinecolor": PALETTE["grid"]}
    layout["yaxis"] = {**layout["yaxis"], "gridcolor": "rgba(0,0,0,0)"}
    figure.update_layout(**layout)
    return figure


def to_jsonable(value: Any) -> Any:
    """Ubah dict/list hasil ``figure.to_dict()`` (berisi numpy/pandas) menjadi struktur JSON biasa."""
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, (pd.Index, pd.Series)):
        return to_jsonable(value.tolist())
    if isinstance(value, np.ndarray):
        if np.issubdtype(value.dtype, np.datetime64):
            return [str(pd.Timestamp(v).date()) for v in value]
        return to_jsonable(value.tolist())
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return to_jsonable(value.item())
    if isinstance(value, float):
        return None if value != value or value in (float("inf"), float("-inf")) else value
    return value


def figure_json(figure: go.Figure) -> dict:
    data = figure.to_dict()
    # Template bawaan plotly (latar putih, warna deret) diganti oleh layout di atas;
    # membuangnya menjaga tampilan sama dengan tema Streamlit dan memperkecil data.
    data.get("layout", {}).pop("template", None)
    return to_jsonable(data)
