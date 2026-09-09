from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from .config import CATEGORIAS, MESES, MESES_ABREV


def numero(valor: float | int | None) -> str:
    if valor is None or pd.isna(valor):
        return "—"
    return f"{int(round(float(valor))):,}".replace(",", ".")


def decimal_br(valor: float | int | None, casas: int = 1) -> str:
    if valor is None or pd.isna(valor):
        return "—"
    return f"{float(valor):.{casas}f}".replace(".", ",")


def percentual(valor: float | int | None, casas: int = 1) -> str:
    if valor is None or pd.isna(valor):
        return "—"
    return f"{float(valor):.{casas}f}%".replace(".", ",")


def signed_percent(valor: float | int | None, casas: int = 1) -> str:
    if valor is None or pd.isna(valor):
        return "—"
    return f"{float(valor):+.{casas}f}%".replace(".", ",")


def mensal(df: pd.DataFrame, start_month: int = 1, end_month: int = 12) -> pd.DataFrame:
    meses = list(range(start_month, end_month + 1))
    if df.empty:
        volume = pd.Series(0, index=meses, dtype=int)
    else:
        volume = df.groupby("mes_referencia").size().reindex(meses, fill_value=0)
    out = pd.DataFrame(
        {
            "mes_num": meses,
            "mes": [MESES[m] for m in meses],
            "mes_abrev": [MESES_ABREV[m] for m in meses],
            "volume": volume.astype(int).values,
        }
    )
    return out


def ranking(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["empresa", "volume", "participacao"])
    out = (
        df.groupby("empresa")
        .size()
        .reset_index(name="volume")
        .sort_values(["volume", "empresa"], ascending=[False, True])
        .reset_index(drop=True)
    )
    total = out["volume"].sum()
    out["participacao"] = out["volume"].div(total).mul(100).fillna(0)
    out["acumulado"] = out["participacao"].cumsum()
    out.insert(0, "posicao", range(1, len(out) + 1))
    return out


def resumo(df: pd.DataFrame, start_month: int = 1, end_month: int = 12) -> dict:
    m = mensal(df, start_month, end_month)
    total = int(m["volume"].sum())
    media = float(m["volume"].mean()) if len(m) else 0.0
    pico = int(m["volume"].max()) if len(m) else 0
    idx = int(m["volume"].idxmax()) if len(m) else 0
    mes_pico = str(m.loc[idx, "mes"]) if len(m) else "—"
    empresas = int(df["empresa"].nunique()) if not df.empty else 0
    desvio = float(m["volume"].std(ddof=0)) if len(m) else 0.0
    cv = (desvio / media * 100) if media else 0.0
    return {
        "total": total,
        "media": media,
        "pico": pico,
        "mes_pico": mes_pico,
        "empresas": empresas,
        "cv": cv,
    }


def top_n_share(df: pd.DataFrame, n: int) -> float:
    rank = ranking(df)
    if rank.empty:
        return 0.0
    return float(rank.head(n)["participacao"].sum())


def crescimento(atual: float, anterior: float) -> float | None:
    if anterior == 0:
        return None if atual == 0 else 100.0
    return (atual / anterior - 1) * 100


def yoy_total(
    dfs: dict[str, pd.DataFrame],
    categorias: Iterable[str],
    year: int,
    start_month: int,
    end_month: int,
) -> float | None:
    if year - 1 not in set(
        int(x)
        for df in dfs.values()
        for x in pd.to_numeric(df["ano_referencia"], errors="coerce").dropna().unique()
    ):
        return None
    atual = 0
    anterior = 0
    for cat in categorias:
        df = dfs[cat]
        atual += len(df[(df["ano_referencia"] == year) & (df["mes_referencia"].between(start_month, end_month))])
        anterior += len(df[(df["ano_referencia"] == year - 1) & (df["mes_referencia"].between(start_month, end_month))])
    return crescimento(atual, anterior)


def yoy_categoria(
    df: pd.DataFrame,
    year: int,
    start_month: int,
    end_month: int,
) -> float | None:
    anos = set(pd.to_numeric(df["ano_referencia"], errors="coerce").dropna().astype(int).unique())
    if year - 1 not in anos:
        return None
    atual = len(df[(df["ano_referencia"] == year) & (df["mes_referencia"].between(start_month, end_month))])
    anterior = len(df[(df["ano_referencia"] == year - 1) & (df["mes_referencia"].between(start_month, end_month))])
    return crescimento(atual, anterior)


def comparacao_mensal(df: pd.DataFrame, year: int, start_month: int, end_month: int) -> pd.DataFrame:
    atual = mensal(
        df[df["ano_referencia"].eq(year)], start_month, end_month
    ).rename(columns={"volume": "volume_atual"})
    anos = set(pd.to_numeric(df["ano_referencia"], errors="coerce").dropna().astype(int).unique())
    atual["volume_anterior"] = np.nan
    if year - 1 in anos:
        anterior = mensal(
            df[df["ano_referencia"].eq(year - 1)], start_month, end_month
        )["volume"].to_numpy()
        atual["volume_anterior"] = anterior
    return atual


def tendencia_recente(df: pd.DataFrame, start_month: int, end_month: int) -> float | None:
    m = mensal(df, start_month, end_month)
    if len(m) < 4:
        return None
    n = min(3, len(m) // 2)
    recente = float(m["volume"].tail(n).mean())
    anterior = float(m["volume"].iloc[-2 * n : -n].mean())
    return crescimento(recente, anterior)


def categoria_resumo(dfs: dict[str, pd.DataFrame], year: int, start_month: int, end_month: int) -> pd.DataFrame:
    total = 0
    dados = []
    for categoria in CATEGORIAS:
        df = dfs[categoria]
        volume = len(df[(df["ano_referencia"].eq(year)) & (df["mes_referencia"].between(start_month, end_month))])
        dados.append({"categoria": categoria, "volume": volume})
        total += volume
    out = pd.DataFrame(dados)
    out["participacao"] = out["volume"].div(total).mul(100).fillna(0)
    return out


def insights_gerais(
    dfs: dict[str, pd.DataFrame],
    year: int,
    start_month: int,
    end_month: int,
    categorias: Iterable[str],
) -> list[dict[str, str]]:
    cats = list(categorias)
    base = []
    for cat in cats:
        df = dfs[cat]
        f = df[(df["ano_referencia"].eq(year)) & (df["mes_referencia"].between(start_month, end_month))]
        if not f.empty:
            base.append((cat, f))
    combinado = pd.concat([x[1] for x in base], ignore_index=True) if base else pd.DataFrame()
    insights: list[dict[str, str]] = []

    if combinado.empty:
        return [{"label": "Leitura", "text": "Não há registros para os filtros selecionados."}]

    rank = ranking(combinado)
    total = len(combinado)
    top5 = top_n_share(combinado, 5)
    if not rank.empty:
        insights.append({
            "label": "Concentração",
            "text": f"As 5 maiores empresas representam {percentual(top5)} do volume no período.",
        })
        insights.append({
            "label": "Principal demanda",
            "text": f"{rank.iloc[0]['empresa']} responde por {percentual(float(rank.iloc[0]['participacao']))} das movimentações.",
        })

    serie = mensal(combinado, start_month, end_month)
    if not serie.empty and int(serie["volume"].max()) > 0:
        pico = serie.loc[serie["volume"].idxmax()]
        insights.append({
            "label": "Pico",
            "text": f"{pico['mes']} concentrou o maior volume, com {numero(int(pico['volume']))} movimentações.",
        })

    crescimentos = []
    for cat in cats:
        g = yoy_categoria(dfs[cat], year, start_month, end_month)
        if g is not None:
            crescimentos.append((cat, g))
    if crescimentos:
        maior = max(crescimentos, key=lambda x: x[1])
        menor = min(crescimentos, key=lambda x: x[1])
        insights.append({
            "label": "Variação",
            "text": f"{maior[0]} é a categoria com maior crescimento contra o mesmo período de {year - 1}: {signed_percent(maior[1])}.",
        })
        if menor[0] != maior[0]:
            insights.append({
                "label": "Atenção",
                "text": f"{menor[0]} apresenta a menor variação interanual entre as categorias: {signed_percent(menor[1])}.",
            })

    # Mantém o bloco curto e executivo.
    return insights[:5]


def dados_empresa(df: pd.DataFrame, empresa: str, year: int, start_month: int, end_month: int) -> dict:
    fatia = df[
        df["empresa"].eq(empresa)
        & df["ano_referencia"].eq(year)
        & df["mes_referencia"].between(start_month, end_month)
    ].copy()
    r = resumo(fatia, start_month, end_month)
    return r
