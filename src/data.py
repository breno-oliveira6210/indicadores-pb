from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]

from .consolidacao import consolidar_tudo

from .config import CATEGORIAS


@st.cache_data(ttl=1800, max_entries=2, show_spinner=False)
def carregar_dados() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carrega e normaliza as três bases de negócio.

    O TTL evita que o dashboard permaneça indefinidamente com uma cópia antiga
    quando os arquivos de origem são atualizados sem novo deploy.
    """
    frames = consolidar_tudo()
    if not isinstance(frames, (tuple, list)) or len(frames) != 3:
        raise ValueError(
            "consolidar_tudo() deve retornar exatamente três DataFrames: "
            "Admissões, Férias e Rescisões."
        )

    return tuple(
        preparar(df, categoria) for df, categoria in zip(frames, CATEGORIAS)
    )  # type: ignore[return-value]


def preparar(df: pd.DataFrame, nome: str) -> pd.DataFrame:
    obrigatorias = {"ano_referencia", "mes_referencia", "empresa"}
    faltantes = obrigatorias - set(df.columns)
    if faltantes:
        raise ValueError(
            f"Base '{nome}' sem colunas obrigatórias: {', '.join(sorted(faltantes))}."
        )

    out = df.copy()
    out["ano_referencia"] = pd.to_numeric(out["ano_referencia"], errors="coerce").astype("Int64")
    out["mes_referencia"] = pd.to_numeric(out["mes_referencia"], errors="coerce").astype("Int64")
    out["empresa"] = (
        out["empresa"]
        .fillna("Empresa não informada")
        .astype(str)
        .str.strip()
        .replace("", "Empresa não informada")
    )
    return out


def datasets() -> dict[str, pd.DataFrame]:
    adm, fer, res = carregar_dados()
    return {"Admissões": adm, "Férias": fer, "Rescisões": res}


def combinar(dfs: dict[str, pd.DataFrame], categorias: Iterable[str] | None = None) -> pd.DataFrame:
    cats = list(categorias or CATEGORIAS)
    partes: list[pd.DataFrame] = []

    for categoria in cats:
        df = dfs.get(categoria)
        if df is None or df.empty:
            continue
        parte = df.copy()
        parte["categoria"] = categoria
        partes.append(parte)

    if not partes:
        return pd.DataFrame()
    return pd.concat(partes, ignore_index=True, sort=False)


def anos_disponiveis(dfs: dict[str, pd.DataFrame]) -> list[int]:
    series = [df["ano_referencia"] for df in dfs.values() if "ano_referencia" in df.columns]
    if not series:
        return []
    valores = (
        pd.concat(series, ignore_index=True)
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )
    return sorted(valores)


def ultimo_mes_disponivel(dfs: dict[str, pd.DataFrame], ano: int) -> int:
    meses: list[int] = []
    for df in dfs.values():
        serie = pd.to_numeric(
            df.loc[df["ano_referencia"] == ano, "mes_referencia"], errors="coerce"
        ).dropna()
        serie = serie[serie.between(1, 12)]
        if not serie.empty:
            meses.append(int(serie.max()))
    return max(meses, default=12)


def filtrar(df: pd.DataFrame, year: int, start_month: int = 1, end_month: int = 12) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    mask = (
        df["ano_referencia"].eq(year)
        & df["mes_referencia"].between(start_month, end_month)
    )
    return df.loc[mask].copy()


def filtrar_por_filtros(
    df: pd.DataFrame,
    *,
    year: int,
    start_month: int,
    end_month: int,
) -> pd.DataFrame:
    return filtrar(df, year, start_month, end_month)


def normalizar_texto(valor: object) -> str:
    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return "".join(c for c in texto if c.isalnum())


def encontrar_coluna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    normalizadas = {normalizar_texto(col): col for col in df.columns}
    for candidato in candidatos:
        chave = normalizar_texto(candidato)
        if chave in normalizadas:
            return normalizadas[chave]
    for candidato in candidatos:
        chave = normalizar_texto(candidato)
        for normalizada, original in normalizadas.items():
            if chave in normalizada or normalizada in chave:
                return original
    return None


DETALHE_CONFIG = {
    "Admissões": [
        (["empresa"], "Empresa"),
        (["funcionario", "colaborador", "nome_funcionario", "nome_colaborador", "nome"], "Funcionário"),
        (["admissao", "data_admissao", "dt_admissao", "data_de_admissao"], "Admissão"),
        (["ano_referencia", "ano"], "Ano"),
    ],
    "Férias": [
        (["empresa"], "Empresa"),
        (["funcionario", "colaborador", "nome_funcionario", "nome_colaborador", "nome"], "Funcionário"),
        (["inicio_gozo", "inicio do gozo", "data_inicio_gozo", "dt_inicio_gozo", "inicio_ferias", "data_inicio", "inicio"], "Início gozo"),
        (["fim_gozo", "fim do gozo", "data_fim_gozo", "dt_fim_gozo", "fim_ferias", "data_fim", "fim"], "Fim gozo"),
        (["ano_referencia", "ano"], "Ano"),
    ],
    "Rescisões": [
        (["empresa"], "Empresa"),
        (["funcionario", "colaborador", "nome_funcionario", "nome_colaborador", "nome"], "Funcionário"),
        (["admissao", "data_admissao", "dt_admissao", "data_de_admissao"], "Admissão"),
        (["demissao", "data_demissao", "dt_demissao", "data_de_demissao"], "Demissão"),
        (["ano_referencia", "ano"], "Ano"),
    ],
}

COLUNAS_DE_DATA = ["Admissão", "Demissão", "Início gozo", "Fim gozo"]


def registros_para_exibicao(df: pd.DataFrame, categoria: str) -> pd.DataFrame:
    selecionadas: dict[str, str] = {}
    for candidatos, nome_saida in DETALHE_CONFIG[categoria]:
        coluna = encontrar_coluna(df, candidatos)
        if coluna is not None and nome_saida not in selecionadas:
            selecionadas[nome_saida] = coluna

    if not selecionadas:
        return pd.DataFrame()

    tabela = df[list(selecionadas.values())].copy()
    tabela = tabela.rename(columns={v: k for k, v in selecionadas.items()})
    ordem = [nome for _, nome in DETALHE_CONFIG[categoria] if nome in tabela.columns]
    tabela = tabela[ordem]

    for coluna in COLUNAS_DE_DATA:
        if coluna not in tabela.columns:
            continue
        serie = tabela[coluna]
        if pd.api.types.is_datetime64_any_dtype(serie):
            datas = pd.to_datetime(serie, errors="coerce")
        else:
            numerica = pd.to_numeric(serie, errors="coerce")
            datas = pd.to_datetime(serie, errors="coerce", dayfirst=True)
            mascara_excel = numerica.between(1, 80000)
            if mascara_excel.any():
                datas_excel = pd.to_datetime(
                    numerica.where(mascara_excel),
                    unit="D",
                    origin="1899-12-30",
                    errors="coerce",
                )
                datas = datas.where(~mascara_excel, datas_excel)
        tabela[coluna] = datas.dt.strftime("%d/%m/%Y").fillna("")

    if "Ano" in tabela.columns:
        tabela["Ano"] = pd.to_numeric(tabela["Ano"], errors="coerce").astype("Int64")

    return tabela
