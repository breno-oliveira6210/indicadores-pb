from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =============================================================================
# CAMINHOS / IMPORTAÇÃO
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from consolidacao import consolidar_tudo


# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Departamento Pessoal | Painel de Indicadores",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# TEMA
# =============================================================================
C = {
    # Base neutra / corporativa
    "bg": "#F5F6F7",
    "surface": "#FFFFFF",
    "text": "#343A40",
    "muted": "#6B7280",
    "border": "#E1E5E8",
    "grid": "#E7EAED",
    "primary": "#3F454B",

    # Categorias: vermelho sóbrio, verde-água e cinza executivo
    "Admissões": "#B84A52",
    "Férias": "#3D918C",
    "Rescisões": "#5B636B",
}

CATEGORIAS = ["Admissões", "Férias", "Rescisões"]
MESES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}
MESES_ABREV = {
    1: "Jan",
    2: "Fev",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Set",
    10: "Out",
    11: "Nov",
    12: "Dez",
}
PLOT_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False,
}


st.markdown(
    f"""
    <style>
        .stApp {{
            background: {C['bg']};
        }}

        .block-container {{
            max-width: 1540px;
            padding: 3.5rem 3rem 3rem !important;
        }}

        section[data-testid="stMain"] .block-container {{
            padding-top: 3.5rem !important;
        }}

        h1, h2, h3, h4 {{
            color: {C['text']} !important;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            letter-spacing: -0.025em;
        }}

        h1 {{
            font-size: 2.05rem !important;
            margin: 0 0 .2rem !important;
        }}

        h2 {{
            font-size: 1.20rem !important;
            margin-top: 0 !important;
        }}

        h3 {{
            font-size: 1.05rem !important;
        }}

        .eyebrow {{
            color: {C['muted']};
            font-size: .76rem;
            font-weight: 800;
            letter-spacing: .10em;
            text-transform: uppercase;
            margin-bottom: .3rem;
        }}

        .subtitle {{
            color: {C['muted']};
            font-size: .94rem;
            line-height: 1.45;
            margin: 0;
        }}

        .soft-note {{
            color: {C['muted']};
            font-size: .80rem;
            margin-top: .25rem;
        }}

        .section-divider {{
            height: 1px;
            background: {C['border']};
            margin: 1.45rem 0 1.55rem;
        }}

        /* Remove controles de moldura do Streamlit na apresentação final */
        header[data-testid="stHeader"] {{
            display: none !important;
        }}

        [data-testid="stSidebarCollapseButton"] {{
            display: none !important;
        }}

        section[data-testid="stSidebar"] button[aria-label="Close sidebar"] {{
            display: none !important;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: {C['surface']};
            border-right: 1px solid {C['border']};
            min-width: 285px !important;
            max-width: 315px !important;
        }}

        section[data-testid="stSidebar"] > div {{
            padding-top: .6rem;
        }}

        /* Aproxima a logo do bloco de título logo abaixo, para um cabeçalho
           mais compacto e visualmente integrado. */
        section[data-testid="stSidebar"] div[data-testid="stImage"] {{
            display: flex;
            justify-content: center;
            margin-bottom: -.5rem;
        }}

        .sidebar-brand {{
            padding: 0 .55rem 1rem;
            margin-top: -.3rem;
            margin-bottom: .9rem;
            border-bottom: 1px solid {C['border']};
            text-align: center;
        }}

        .sidebar-brand-title {{
            color: {C['text']};
            font-size: 1.02rem;
            font-weight: 800;
            margin-top: 0;
        }}

        .sidebar-brand-subtitle {{
            color: {C['muted']};
            font-size: .82rem;
            margin-top: .12rem;
        }}

        /* Selectors */
        div[data-baseweb="select"] > div {{
            border-color: {C['border']} !important;
            border-radius: 9px !important;
            background: {C['surface']} !important;
            min-height: 40px;
        }}

        div[data-baseweb="select"] > div:hover {{
            border-color: #B7C2D0 !important;
        }}

        /* Navigation */
        div[role="radiogroup"] label {{
            border-radius: 9px;
            padding: .5rem .55rem;
            font-size: .94rem;
        }}

        div[role="radiogroup"] label:hover {{
            background: #F2F5F8;
        }}

        /* KPI */
        div[data-testid="stMetric"] {{
            background: {C['surface']};
            border: 1px solid {C['border']};
            border-radius: 14px;
            padding: .95rem 1.05rem;
            min-height: 100px;
            box-shadow: 0 1px 2px rgba(16,24,40,.03);
        }}

        div[data-testid="stMetricLabel"] p {{
            color: {C['muted']} !important;
            font-size: .86rem !important;
            font-weight: 650 !important;
        }}

        div[data-testid="stMetricValue"] {{
            color: {C['text']} !important;
            font-size: 1.75rem !important;
        }}

        /* Dataframe */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {C['border']};
            border-radius: 10px;
            overflow: hidden;
        }}

        /* Expander */
        details[data-testid="stExpander"] {{
            border: 1px solid {C['border']};
            border-radius: 10px;
            background: {C['surface']};
        }}

        #MainMenu, footer {{
            visibility: hidden;
        }}

        @media (max-width: 1050px) {{
            .block-container {{
                padding-left: 1.25rem;
                padding-right: 1.25rem;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# FUNÇÕES DE DADOS
# =============================================================================
@st.cache_data(show_spinner=False)
def carregar_dados():
    return consolidar_tudo()


def preparar(df: pd.DataFrame, nome: str) -> pd.DataFrame:
    obrigatorias = {"ano_referencia", "mes_referencia", "empresa"}
    faltantes = obrigatorias - set(df.columns)
    if faltantes:
        raise ValueError(
            f"Base '{nome}' sem colunas obrigatórias: {', '.join(sorted(faltantes))}."
        )

    out = df.copy()
    out["ano_referencia"] = pd.to_numeric(
        out["ano_referencia"], errors="coerce"
    ).astype("Int64")
    out["mes_referencia"] = pd.to_numeric(
        out["mes_referencia"], errors="coerce"
    ).astype("Int64")
    out["empresa"] = (
        out["empresa"]
        .fillna("Empresa não informada")
        .astype(str)
        .str.strip()
        .replace("", "Empresa não informada")
    )
    return out


def por_ano(df: pd.DataFrame, ano: int) -> pd.DataFrame:
    return df.loc[df["ano_referencia"] == ano].copy()


def mensal(df: pd.DataFrame) -> pd.DataFrame:
    serie = (
        df.groupby("mes_referencia")
        .size()
        .reindex(range(1, 13), fill_value=0)
    )
    return pd.DataFrame(
        {
            "mes_num": range(1, 13),
            "mes": [MESES[i] for i in range(1, 13)],
            "mes_abrev": [MESES_ABREV[i] for i in range(1, 13)],
            "volume": serie.values.astype(int),
        }
    )


def ranking(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("empresa")
        .size()
        .reset_index(name="volume")
        .sort_values(["volume", "empresa"], ascending=[False, True])
        .reset_index(drop=True)
    )


def numero(valor) -> str:
    return f"{int(round(valor)):,}".replace(",", ".")


def decimal_br(valor: float, casas: int = 1) -> str:
    """Formata um número decimal no padrão brasileiro (vírgula), ex.: 8,3."""
    return f"{valor:.{casas}f}".replace(".", ",")


def ultimo_mes(df: pd.DataFrame) -> int | None:
    if df.empty:
        return None
    serie = pd.to_numeric(df["mes_referencia"], errors="coerce").dropna().astype(int)
    serie = serie[serie.between(1, 12)]
    return int(serie.max()) if not serie.empty else None


def nome_curto(nome: str, limite: int = 34) -> str:
    """Exibe apenas os dois primeiros termos da razão social no gráfico."""
    nome = str(nome).strip()
    if not nome:
        return "Empresa"

    termos = nome.split()
    if len(termos) <= 2:
        return nome

    return " ".join(termos[:2])


def ranking_grafico(df: pd.DataFrame, limite: int = 12) -> pd.DataFrame:
    """
    Seleciona as N maiores empresas e devolve em ordem CRESCENTE de volume.
    Isso é proposital: em um gráfico de barras horizontais, a ordem padrão
    do Plotly desenha a primeira linha do dataframe embaixo e a última em
    cima — então, com a menor embaixo e a maior por último, a maior empresa
    acaba aparecendo no topo do gráfico (ordem decrescente visualmente).
    """
    out = df.head(limite).copy().sort_values("volume", ascending=True)
    out["empresa_label"] = out["empresa"].map(nome_curto)
    return out


def consolidado_ano(df_adm, df_fer, df_res, ano: int) -> pd.DataFrame:
    partes = []
    for categoria, df in zip(CATEGORIAS, [df_adm, df_fer, df_res]):
        fatia = por_ano(df, ano)
        if not fatia.empty:
            x = fatia[["empresa", "mes_referencia"]].copy()
            x["categoria"] = categoria
            partes.append(x)

    if not partes:
        return pd.DataFrame(columns=["empresa", "mes_referencia", "categoria"])

    return pd.concat(partes, ignore_index=True)


# =============================================================================
# DETALHAMENTO DE REGISTROS
# =============================================================================
def normalizar_texto(valor: object) -> str:
    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return "".join(c for c in texto if c.isalnum())


def encontrar_coluna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    """Localiza uma coluna pelo nome, ignorando caixa, acentos e separadores."""
    normalizadas = {normalizar_texto(col): col for col in df.columns}

    # 1) correspondência exata normalizada
    for candidato in candidatos:
        chave = normalizar_texto(candidato)
        if chave in normalizadas:
            return normalizadas[chave]

    # 2) correspondência parcial controlada
    for candidato in candidatos:
        chave = normalizar_texto(candidato)
        for normalizada, original in normalizadas.items():
            if chave in normalizada or normalizada in chave:
                return original

    return None


# Observação: a coluna "Código" foi removida deste mapeamento. A base tratada
# não guarda um identificador de funcionário — o que existia (codigo_empresa)
# já aparece de forma clara na coluna "Empresa", então mantê-la como "Código"
# só duplicava a informação com um rótulo que induzia a erro.
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
    # Corrigido: antes esta lista era uma cópia da de Férias e procurava por
    # "início/fim de gozo" (que não existe em Rescisões), então a tabela de
    # detalhamento desta aba sempre vinha sem nenhuma data. Agora usa as
    # colunas reais da base de Rescisões: data_admissao e data_demissao.
    "Rescisões": [
        (["empresa"], "Empresa"),
        (["funcionario", "colaborador", "nome_funcionario", "nome_colaborador", "nome"], "Funcionário"),
        (["admissao", "data_admissao", "dt_admissao", "data_de_admissao"], "Admissão"),
        (["demissao", "data_demissao", "dt_demissao", "data_de_demissao"], "Demissão"),
        (["ano_referencia", "ano"], "Ano"),
    ],
}

# Colunas que recebem formatação de data (dd/mm/aaaa) na tabela de detalhamento
COLUNAS_DE_DATA = ["Admissão", "Demissão", "Início gozo", "Fim gozo"]


def registros_para_exibicao(df: pd.DataFrame, categoria: str) -> pd.DataFrame:
    """Retorna somente as colunas solicitadas, com os nomes executivos definidos."""
    selecionadas = {}
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

    # Datas em padrão brasileiro, sem horário.
    # Trata datetime, texto e números no padrão de data serial do Excel.
    for coluna in COLUNAS_DE_DATA:
        if coluna not in tabela.columns:
            continue

        serie = tabela[coluna]

        if pd.api.types.is_datetime64_any_dtype(serie):
            datas = pd.to_datetime(serie, errors="coerce")
        else:
            numerica = pd.to_numeric(serie, errors="coerce")
            datas = pd.to_datetime(serie, errors="coerce", dayfirst=True)

            # Se forem números típicos de data serial do Excel, usa a origem correta.
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


# =============================================================================
# FUNÇÕES DE GRÁFICOS
# =============================================================================
def base_layout(fig, altura: int):
    fig.update_layout(
        height=altura,
        margin=dict(t=18, b=12, l=10, r=18),
        font=dict(
            family='Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',
            size=12,
            color=C["text"],
        ),
        plot_bgcolor=C["surface"],
        paper_bgcolor=C["surface"],
        hoverlabel=dict(
            bgcolor=C["surface"],
            bordercolor=C["border"],
            font=dict(color=C["muted"]),
        ),
    )
    return fig


def grafico_resumo(df_adm_ano, df_fer_ano, df_res_ano):
    base = pd.DataFrame(
        {
            "Mês": [MESES[i] for i in range(1, 13)],
            "Admissões": mensal(df_adm_ano)["volume"],
            "Férias": mensal(df_fer_ano)["volume"],
            "Rescisões": mensal(df_res_ano)["volume"],
        }
    )
    melt = base.melt(
        id_vars="Mês",
        value_vars=CATEGORIAS,
        var_name="Categoria",
        value_name="Volume",
    )

    fig = px.bar(
        melt,
        x="Mês",
        y="Volume",
        color="Categoria",
        barmode="group",
        color_discrete_map={k: C[k] for k in CATEGORIAS},
        category_orders={"Mês": list(MESES.values()), "Categoria": CATEGORIAS},
        template="plotly_white",
    )
    fig.update_traces(
        marker_line_width=0,
        hovertemplate="%{x}<br>%{fullData.name}: <b>%{y}</b><extra></extra>",
    )
    fig.update_xaxes(
        title=None,
        fixedrange=True,
        showgrid=False,
        tickfont=dict(size=11, color=C["muted"]),
    )
    fig.update_yaxes(
        title=None,
        fixedrange=True,
        showgrid=True,
        gridcolor=C["grid"],
        zeroline=False,
        showticklabels=False,
    )
    base_layout(fig, 360).update_layout(
        legend=dict(
            title=None,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        bargap=.16,
        bargroupgap=.06,
    )
    return fig


def grafico_mensal(df: pd.DataFrame, cor: str, altura: int = 330):
    base = mensal(df)
    fig = px.bar(
        base,
        x="mes_abrev",
        y="volume",
        text="volume",
        category_orders={"mes_abrev": list(MESES_ABREV.values())},
        template="plotly_white",
    )
    fig.update_traces(
        marker_color=cor,
        marker_line_width=0,
        textposition="outside",
        hovertemplate="%{x}: <b>%{y}</b><extra></extra>",
    )
    ymax = int(base["volume"].max())
    limite = max(5, int(ymax * 1.25) if ymax else 5)
    fig.update_xaxes(
        title=None,
        fixedrange=True,
        showgrid=False,
        tickfont=dict(size=11, color=C["muted"]),
    )
    fig.update_yaxes(
        title=None,
        fixedrange=True,
        range=[0, limite],
        showticklabels=False,
        showgrid=True,
        gridcolor=C["grid"],
        zeroline=False,
    )
    base_layout(fig, altura).update_layout(bargap=.28)
    return fig


def grafico_ranking(df: pd.DataFrame, cor: str, limite: int = 12):
    top = ranking_grafico(df, limite)
    fig = px.bar(
        top,
        x="volume",
        y="empresa_label",
        orientation="h",
        text="volume",
        template="plotly_white",
    )
    fig.update_traces(
        marker_color=cor,
        marker_line_width=0,
        textposition="outside",
        hovertemplate="<b>%{customdata}</b><br>Volume: <b>%{x}</b><extra></extra>",
        customdata=top["empresa"],
    )
    vmax = int(top["volume"].max()) if not top.empty else 0
    limite_x = max(5, int(vmax * 1.18) if vmax else 5)
    # CORRIGIDO: antes havia "autorange='reversed'" aqui, o que somado à
    # ordenação crescente do dataframe (ranking_grafico) colocava a MENOR
    # empresa no topo do gráfico. Como já ordenamos os dados de propósito
    # (menor embaixo, maior por último), a ordem padrão do eixo já entrega
    # a maior empresa no topo — por isso o "reversed" foi removido.
    fig.update_yaxes(
        title=None,
        fixedrange=True,
        tickfont=dict(size=11, color=C["text"]),
    )
    fig.update_xaxes(
        title=None,
        fixedrange=True,
        range=[0, limite_x],
        showticklabels=False,
        showgrid=True,
        gridcolor=C["grid"],
        zeroline=False,
    )
    base_layout(fig, max(300, 36 * len(top) + 70))
    return fig


# =============================================================================
# CARREGAMENTO
# =============================================================================
try:
    df_adm_raw, df_fer_raw, df_res_raw = carregar_dados()
    df_adm = preparar(df_adm_raw, "Admissões")
    df_fer = preparar(df_fer_raw, "Férias")
    df_res = preparar(df_res_raw, "Rescisões")
except Exception as exc:
    st.error("Não foi possível carregar os dados do dashboard.")
    st.exception(exc)
    st.stop()

anos = sorted(
    pd.concat(
        [
            df_adm["ano_referencia"],
            df_fer["ano_referencia"],
            df_res["ano_referencia"],
        ],
        ignore_index=True,
    )
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

if not anos:
    st.warning("Não existem anos de referência disponíveis.")
    st.stop()


# =============================================================================
# SIDEBAR — NAVEGAÇÃO E FILTRO GLOBAL
# =============================================================================
with st.sidebar:
    logo = BASE_DIR / "pb_logo.png"
    if logo.exists():
        logo_col1, logo_col2, logo_col3 = st.columns([0.25, 0.5, 0.25])
        with logo_col2:
            st.image(str(logo), width=110)

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">Departamento Pessoal</div>
            <div class="sidebar-brand-subtitle">Painel de Indicadores</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Navegação**")
    aba = st.radio(
        "Navegação",
        ["Visão Geral", *CATEGORIAS],
        index=0,
        label_visibility="collapsed",
        key="aba_dashboard",
    )

    st.markdown("**Ano de referência**")
    ano = st.selectbox(
        "Ano de referência",
        anos,
        index=len(anos) - 1,
        label_visibility="collapsed",
        key="ano_dashboard",
    )

    st.markdown(
        "<div class='soft-note'>O filtro de ano se aplica a toda a página selecionada.</div>",
        unsafe_allow_html=True,
    )


# =============================================================================
# FUNÇÕES DE RENDERIZAÇÃO
# =============================================================================
def cabecalho(eyebrow: str, titulo: str, subtitulo: str, referencia: str | None = None):
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(f"# {titulo}")
    st.markdown(f'<p class="subtitle">{subtitulo}</p>', unsafe_allow_html=True)
    if referencia:
        st.markdown(f'<div class="soft-note">{referencia}</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


def tabela_ranking(df_rank: pd.DataFrame):
    tabela = df_rank.rename(
        columns={"empresa": "Empresa", "volume": "Volume"}
    ).copy()
    tabela.insert(0, "Posição", range(1, len(tabela) + 1))
    total = tabela["Volume"].sum()
    tabela["Participação"] = (
        (tabela["Volume"] / total * 100).map(lambda x: f"{decimal_br(x)}%")
        if total
        else "0,0%"
    )
    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        height=min(430, 60 + len(tabela) * 35),
        column_config={
            "Posição": st.column_config.NumberColumn(width="small"),
            "Volume": st.column_config.NumberColumn(format="%d"),
            "Participação": st.column_config.TextColumn(width="small"),
        },
    )


def render_resumo():
    da = por_ano(df_adm, ano)
    df = por_ano(df_fer, ano)
    dr = por_ano(df_res, ano)

    totais = {
        "Admissões": len(da),
        "Férias": len(df),
        "Rescisões": len(dr),
    }
    total = sum(totais.values())
    ultimo = max(
        filter(None, [ultimo_mes(da), ultimo_mes(df), ultimo_mes(dr)]),
        default=None,
    )
    referencia = f"Última atualização: {MESES[ultimo]} de {ano}." if ultimo else None

    cabecalho(
        "Visão geral",
        f"Departamento Pessoal — {ano}",
        "Movimentações de pessoal e concentração por empresa.",
        referencia,
    )

    k1, k2, k3, k4 = st.columns(4, gap="medium")
    k1.metric("Volume total", numero(total))
    k2.metric("Admissões", numero(totais["Admissões"]))
    k3.metric("Férias", numero(totais["Férias"]))
    k4.metric("Rescisões", numero(totais["Rescisões"]))

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.55, 1], gap="large")

    with c1:
        st.markdown('<div class="eyebrow">Indicadores</div>', unsafe_allow_html=True)
        st.subheader("Distribuição mensal por categoria")
        st.plotly_chart(
            grafico_resumo(da, df, dr),
            use_container_width=True,
            config=PLOT_CONFIG,
        )

    with c2:
        st.markdown('<div class="eyebrow">Concentração</div>', unsafe_allow_html=True)
        st.subheader("Maiores empresas por volume")
        base = consolidado_ano(df_adm, df_fer, df_res, ano)
        rank = ranking(base)

        if rank.empty:
            st.info("Não há empresas com registros para o ano selecionado.")
        else:
            st.plotly_chart(
                grafico_ranking(rank, C["primary"], 10),
                use_container_width=True,
                config=PLOT_CONFIG,
            )
            with st.expander("Ver ranking completo"):
                tabela_ranking(rank)


def render_categoria(nome: str, df_base: pd.DataFrame):
    cor = C[nome]
    df = por_ano(df_base, ano)

    cabecalho(
        "Visão analítica",
        f"{nome} — {ano}",
        f"Evolução mensal, concentração por empresa e análise individual de {nome.lower()}.",
        f"Base com {numero(len(df))} registros no ano.",
    )

    if df.empty:
        st.warning(f"Não há registros de {nome.lower()} para o ano de {ano}.")
        return

    m = mensal(df)
    total = len(df)
    media = m["volume"].mean()
    pico = int(m["volume"].max())
    mes_pico = m.loc[m["volume"].idxmax(), "mes"]
    empresas = df["empresa"].nunique()

    k1, k2, k3, k4 = st.columns(4, gap="medium")
    k1.metric("Volume no ano", numero(total))
    k2.metric("Média mensal", decimal_br(media))
    k3.metric("Maior volume mensal", numero(pico))
    k4.metric("Empresas atendidas", numero(empresas))

    st.markdown(
        f'<div class="soft-note">Maior volume registrado em {mes_pico}.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Evolução</div>', unsafe_allow_html=True)
    st.subheader("Tendência e sazonalidade mensal")
    st.plotly_chart(
        grafico_mensal(df, cor),
        use_container_width=True,
        config=PLOT_CONFIG,
    )

    st.markdown("<div style='height:.55rem'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.05, 1], gap="large")
    rank = ranking(df)

    with c1:
        st.markdown('<div class="eyebrow">Concentração</div>', unsafe_allow_html=True)
        st.subheader("Maiores empresas por volume")
        st.plotly_chart(
            grafico_ranking(rank, cor, 12),
            use_container_width=True,
            config=PLOT_CONFIG,
        )
        with st.expander("Ver ranking completo"):
            tabela_ranking(rank)

    with c2:
        st.markdown('<div class="eyebrow">Análise individual</div>', unsafe_allow_html=True)
        st.subheader("Por empresa")

        empresas_disponiveis = rank["empresa"].tolist()
        empresa = st.selectbox(
            "Empresa",
            empresas_disponiveis,
            format_func=lambda x: nome_curto(x, 50),
            key=f"empresa_{nome}_{ano}",
        )

        df_emp = df.loc[df["empresa"] == empresa].copy()
        total_emp = len(df_emp)
        participacao = total_emp / total * 100 if total else 0
        m_emp = mensal(df_emp)
        pico_emp = int(m_emp["volume"].max())

        a, b, c = st.columns(3)
        a.metric("Volume", numero(total_emp))
        b.metric("Participação", f"{decimal_br(participacao)}%")
        c.metric("Pico mensal", numero(pico_emp))

        st.plotly_chart(
            grafico_mensal(df_emp, cor, 285),
            use_container_width=True,
            config=PLOT_CONFIG,
        )

        with st.expander("Detalhar registros da empresa"):
            tabela = registros_para_exibicao(df_emp, nome)
            if tabela.empty:
                st.info("Não foi possível localizar as colunas de detalhamento esperadas na base.")
            else:
                config_colunas = {}
                for coluna in ["Empresa", "Funcionário"]:
                    if coluna in tabela.columns:
                        config_colunas[coluna] = st.column_config.TextColumn(coluna, width="medium")
                for coluna in COLUNAS_DE_DATA:
                    if coluna in tabela.columns:
                        config_colunas[coluna] = st.column_config.TextColumn(coluna, width="small")
                if "Ano" in tabela.columns:
                    config_colunas["Ano"] = st.column_config.NumberColumn("Ano", width="small", format="%d")

                st.dataframe(
                    tabela,
                    use_container_width=True,
                    hide_index=True,
                    height=320,
                    column_config=config_colunas,
                )


# =============================================================================
# EXECUÇÃO
# =============================================================================
if aba == "Visão Geral":
    render_resumo()
elif aba == "Admissões":
    render_categoria("Admissões", df_adm)
elif aba == "Férias":
    render_categoria("Férias", df_fer)
else:
    render_categoria("Rescisões", df_res)