from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .analytics import mensal, ranking
from .config import COLORS, MESES_ABREV


def _layout(fig, height=330):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=18, t=14, b=14),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family='Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif', color=COLORS["text"], size=11),
        showlegend=False,
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, fixedrange=True, title=None)
    fig.update_yaxes(showgrid=True, gridcolor=COLORS["grid"], zeroline=False, fixedrange=True, title=None)
    return fig


def grafico_total_mensal(df: pd.DataFrame, start: int, end: int):
    m = mensal(df, start, end)
    cats = []
    for categoria in ["Admissões", "Férias", "Rescisões"]:
        if "categoria" in df.columns and df.loc[df["categoria"] == categoria].shape[0]:
            cats.append(categoria)
    if not cats:
        cats = ["Volume"]

    fig = go.Figure()
    if cats != ["Volume"]:
        for cat in cats:
            mc = mensal(df[df["categoria"].eq(cat)], start, end)
            fig.add_trace(go.Scatter(x=mc["mes_abrev"], y=mc["volume"], mode="lines+markers", name=cat,
                                     line=dict(color=COLORS[cat], width=2.5), marker=dict(size=5),
                                     hovertemplate=f"{cat}: <b>%{{y}}</b><extra></extra>"))
    else:
        fig.add_trace(go.Scatter(x=m["mes_abrev"], y=m["volume"], mode="lines+markers", name="Volume",
                                 line=dict(color=COLORS["primary"], width=2.5), marker=dict(size=5),
                                 hovertemplate="Volume: <b>%{y}</b><extra></extra>"))
    fig.update_layout(showlegend=True, legend=dict(orientation="h", x=0, y=1.12), hovermode="x unified")
    fig.update_yaxes(showticklabels=True, tickformat=",.")
    return _layout(fig, 350)


def grafico_composicao(df: pd.DataFrame, start: int, end: int):
    if df.empty:
        return _layout(go.Figure(), 260)
    base = df.groupby("categoria").size().reindex(["Admissões", "Férias", "Rescisões"], fill_value=0).reset_index(name="volume")
    fig = go.Figure(go.Bar(
        x=base["volume"], y=base["categoria"], orientation="h",
        marker_color=[COLORS[x] for x in base["categoria"]],
        text=base["volume"], textposition="outside",
        hovertemplate="%{y}: <b>%{x}</b><extra></extra>"
    ))
    fig.update_yaxes(categoryorder="array", categoryarray=["Rescisões", "Férias", "Admissões"])
    return _layout(fig, 265)


def grafico_ranking(df: pd.DataFrame, limite: int = 10, color: str | None = None):
    r = ranking(df).head(limite).sort_values("volume", ascending=True)
    fig = go.Figure(go.Bar(
        x=r["volume"], y=r["empresa"].str.slice(0, 34), orientation="h",
        marker_color=color or COLORS["primary"],
        text=r["volume"], textposition="outside",
        customdata=r["empresa"],
        hovertemplate="<b>%{customdata}</b><br>Volume: <b>%{x}</b><extra></extra>"
    ))
    fig.update_xaxes(showticklabels=False)
    return _layout(fig, max(320, 38 * len(r) + 70))


def grafico_categoria_mensal(df: pd.DataFrame, categoria: str, start: int, end: int):
    m = mensal(df, start, end)
    fig = go.Figure(go.Scatter(
        x=m["mes_abrev"], y=m["volume"], mode="lines+markers+text",
        text=m["volume"], textposition="top center",
        line=dict(color=COLORS[categoria], width=2.8), marker=dict(color=COLORS[categoria], size=6),
        hovertemplate="%{x}: <b>%{y}</b><extra></extra>"
    ))
    return _layout(fig, 340)


def grafico_empresa_mensal(df: pd.DataFrame, start: int, end: int, color: str | None = None):
    m = mensal(df, start, end)
    fig = go.Figure(go.Bar(
        x=m["mes_abrev"], y=m["volume"],
        marker_color=color or COLORS["primary"],
        text=m["volume"], textposition="outside",
        hovertemplate="%{x}: <b>%{y}</b><extra></extra>"
    ))
    fig.update_yaxes(showticklabels=False)
    return _layout(fig, 300)
