from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from .analytics import mensal, numero, percentual, ranking
from .config import COLORS, MESES_ABREV


def base_layout(fig: go.Figure, height: int, *, title: str | None = None) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(t=42 if title else 12, b=28, l=8, r=8),
        font=dict(family='Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif', size=12, color=COLORS["text"]),
        plot_bgcolor=COLORS["surface"],
        paper_bgcolor=COLORS["surface"],
        hoverlabel=dict(bgcolor=COLORS["surface"], bordercolor=COLORS["border"], font=dict(color=COLORS["text"])),
        hovermode="x unified",
        title=dict(text=title, x=0, xanchor="left", y=0.99, font=dict(size=15, color=COLORS["text"])) if title else None,
        showlegend=False,
    )
    return fig


def grafico_evolucao_geral(df: pd.DataFrame, year: int, start_month: int, end_month: int) -> go.Figure:
    m = mensal(df[df["ano_referencia"].eq(year)], start_month, end_month)
    m["media_movel"] = m["volume"].rolling(3, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=m["mes_abrev"],
            y=m["volume"],
            name="Movimentações",
            marker_color=COLORS["primary"],
            opacity=0.88,
            hovertemplate="<b>%{x}</b><br>Volume: %{y}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=m["mes_abrev"],
            y=m["media_movel"],
            mode="lines",
            name="Média móvel",
            line=dict(color=COLORS["negative"], width=2.5),
            hovertemplate="Média móvel: <b>%{y:.1f}</b><extra></extra>",
        )
    )
    ymax = max(int(m["volume"].max()) if len(m) else 0, 1)
    fig.update_xaxes(title=None, fixedrange=True, showgrid=False, tickfont=dict(size=11, color=COLORS["muted"]), categoryorder="array", categoryarray=list(m["mes_abrev"]))
    fig.update_yaxes(title=None, fixedrange=True, showgrid=True, gridcolor=COLORS["grid"], zeroline=False, showticklabels=False, rangemode="tozero")
    fig.update_layout(
        barmode="overlay",
        bargap=.35,
        showlegend=True,
        legend=dict(orientation="h", x=0, y=1.12, xanchor="left", yanchor="bottom", font=dict(size=11)),
        yaxis=dict(range=[0, ymax * 1.18]),
    )
    return base_layout(fig, 360)


def grafico_composicao_categorias(df: pd.DataFrame, start_month: int, end_month: int) -> go.Figure:
    m = monthly_category(df, start_month, end_month)
    fig = go.Figure()
    categorias_presentes = [c for c in ["Admissões", "Férias", "Rescisões"] if c in m.columns and int(m[c].sum()) > 0]
    for categoria in categorias_presentes:
        fig.add_trace(
            go.Bar(
                x=m["mes_abrev"],
                y=m[categoria],
                name=categoria,
                marker_color=COLORS[categoria],
                hovertemplate=f"{categoria}: <b>%{{y}}</b><extra></extra>",
            )
        )
    fig.update_layout(barmode="stack", bargap=.28, showlegend=bool(categorias_presentes), legend=dict(orientation="h", x=0, y=1.12, xanchor="left", yanchor="bottom", font=dict(size=10)))
    fig.update_xaxes(title=None, fixedrange=True, showgrid=False, tickfont=dict(size=10, color=COLORS["muted"]))
    fig.update_yaxes(title=None, fixedrange=True, showgrid=True, gridcolor=COLORS["grid"], showticklabels=False, zeroline=False)
    return base_layout(fig, 330)


def monthly_category(df: pd.DataFrame, start_month: int, end_month: int) -> pd.DataFrame:
    meses = list(range(start_month, end_month + 1))
    out = pd.DataFrame({"mes_num": meses, "mes_abrev": [MESES_ABREV[m] for m in meses]})
    for categoria in ["Admissões", "Férias", "Rescisões"]:
        subset = df[df["categoria"].eq(categoria)] if "categoria" in df.columns else pd.DataFrame()
        s = subset.groupby("mes_referencia").size().reindex(meses, fill_value=0)
        out[categoria] = s.astype(int).values
    return out


def grafico_mix_categorias(df: pd.DataFrame) -> go.Figure:
    if df.empty or "categoria" not in df.columns:
        return base_layout(go.Figure(), 180)
    agg = df.groupby("categoria").size().reindex(["Admissões", "Férias", "Rescisões"], fill_value=0).reset_index(name="volume")
    total = agg["volume"].sum()
    agg["participacao"] = agg["volume"].div(total).mul(100).fillna(0)
    fig = go.Figure()
    for row in agg.itertuples(index=False):
        if int(row.volume) <= 0:
            continue
        fig.add_trace(
            go.Bar(
                x=[float(row.participacao)],
                y=["Mix de demandas"],
                orientation="h",
                name=row.categoria,
                marker_color=COLORS[row.categoria],
                customdata=[[row.categoria, int(row.volume)]],
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} registros • %{x:.1f}%<extra></extra>",
            )
        )
    fig.update_layout(barmode="stack", showlegend=False)
    fig.update_xaxes(range=[0, 100], showticklabels=False, showgrid=False, fixedrange=True, title=None)
    fig.update_yaxes(showticklabels=False, showgrid=False, fixedrange=True, title=None)
    return base_layout(fig, 150)


def grafico_ranking(df: pd.DataFrame, limite: int = 10, color: str | None = None) -> go.Figure:
    r = ranking(df).head(limite).sort_values("volume", ascending=True)
    fig = go.Figure()
    if r.empty:
        return base_layout(fig, 260)
    fig.add_trace(
        go.Bar(
            x=r["volume"],
            y=r["empresa"],
            orientation="h",
            marker_color=color or COLORS["primary"],
            text=r["volume"].map(lambda x: numero(x)),
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Volume: %{x}<br>Participação: %{customdata:.1f}%<extra></extra>",
            customdata=r["participacao"],
        )
    )
    xmax = max(int(r["volume"].max()) if len(r) else 0, 1)
    fig.update_xaxes(title=None, fixedrange=True, showticklabels=False, showgrid=True, gridcolor=COLORS["grid"], zeroline=False, range=[0, xmax * 1.22])
    fig.update_yaxes(title=None, fixedrange=True, tickfont=dict(size=10.5, color=COLORS["text"]), showgrid=False)
    return base_layout(fig, max(290, 34 * len(r) + 70))


def grafico_pareto(df: pd.DataFrame, limite: int = 12) -> go.Figure:
    r = ranking(df).head(limite).copy()
    fig = go.Figure()
    if r.empty:
        return base_layout(fig, 290)
    fig.add_trace(go.Bar(x=r["empresa"], y=r["volume"], name="Volume", marker_color=COLORS["primary"], hovertemplate="<b>%{x}</b><br>Volume: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=r["empresa"], y=r["acumulado"], name="Acumulado", yaxis="y2", mode="lines+markers", line=dict(color=COLORS["negative"], width=2), marker=dict(size=6), hovertemplate="Acumulado: <b>%{y:.1f}%</b><extra></extra>"))
    fig.update_layout(
        yaxis=dict(title=None, showgrid=True, gridcolor=COLORS["grid"], showticklabels=False, rangemode="tozero"),
        yaxis2=dict(title=None, overlaying="y", side="right", range=[0, 105], showgrid=False, ticksuffix="%", tickfont=dict(color=COLORS["muted"])),
        xaxis=dict(title=None, fixedrange=True, tickangle=-35, tickfont=dict(size=9.5, color=COLORS["text"])),
        showlegend=True,
        legend=dict(orientation="h", x=0, y=1.12, xanchor="left", yanchor="bottom", font=dict(size=10)),
    )
    return base_layout(fig, 330)


def grafico_categoria(df: pd.DataFrame, year: int, start_month: int, end_month: int, color: str) -> go.Figure:
    m = mensal(df[df["ano_referencia"].eq(year)], start_month, end_month)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=m["mes_abrev"],
            y=m["volume"],
            marker_color=color,
            text=m["volume"],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{x}</b><br>Volume: %{y}<extra></extra>",
        )
    )
    fig.update_xaxes(title=None, fixedrange=True, showgrid=False, tickfont=dict(size=11, color=COLORS["muted"]))
    fig.update_yaxes(title=None, fixedrange=True, showgrid=True, gridcolor=COLORS["grid"], showticklabels=False, zeroline=False, rangemode="tozero")
    return base_layout(fig, 350)


def grafico_categoria_comparado(df: pd.DataFrame, year: int, start_month: int, end_month: int, color: str) -> go.Figure:
    atual = mensal(df[df["ano_referencia"].eq(year)], start_month, end_month)
    anterior = mensal(df[df["ano_referencia"].eq(year - 1)], start_month, end_month)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=atual["mes_abrev"], y=atual["volume"], mode="lines+markers", line=dict(color=color, width=3), marker=dict(size=7), name=str(year), hovertemplate=f"{year}: <b>%{{y}}</b><extra></extra>"))
    if (df["ano_referencia"].eq(year - 1)).any():
        fig.add_trace(go.Scatter(x=anterior["mes_abrev"], y=anterior["volume"], mode="lines", line=dict(color=COLORS["muted"], width=2, dash="dash"), name=str(year - 1), hovertemplate=f"{year - 1}: <b>%{{y}}</b><extra></extra>"))
    fig.update_xaxes(title=None, fixedrange=True, showgrid=False, tickfont=dict(size=11, color=COLORS["muted"]))
    fig.update_yaxes(title=None, fixedrange=True, showgrid=True, gridcolor=COLORS["grid"], showticklabels=False, zeroline=False)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", x=0, y=1.12, xanchor="left", yanchor="bottom", font=dict(size=11)))
    return base_layout(fig, 360)


def grafico_empresa_periodo(df: pd.DataFrame, year: int, start_month: int, end_month: int, empresa: str, color: str) -> go.Figure:
    fatia = df[(df["empresa"].eq(empresa)) & (df["ano_referencia"].eq(year))]
    return grafico_categoria(fatia, year, start_month, end_month, color)


def grafico_empresa_mix(df: pd.DataFrame, empresa: str) -> go.Figure:
    base = df[df["empresa"].eq(empresa)].groupby("categoria").size().reindex(["Admissões", "Férias", "Rescisões"], fill_value=0).reset_index(name="volume")
    total = base["volume"].sum()
    base["participacao"] = base["volume"].div(total).mul(100).fillna(0)
    fig = px.bar(base, x="participacao", y="categoria", orientation="h", text="participacao", category_orders={"categoria": ["Admissões", "Férias", "Rescisões"]})
    fig.update_traces(marker_color=[COLORS[x] for x in base["categoria"]], texttemplate="%{text:.1f}%", textposition="outside", hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>")
    fig.update_xaxes(title=None, fixedrange=True, range=[0, max(100, float(base["participacao"].max()) * 1.18)], showgrid=True, gridcolor=COLORS["grid"], showticklabels=False)
    fig.update_yaxes(title=None, fixedrange=True, showgrid=False)
    return base_layout(fig, 230)
