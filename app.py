from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.analytics import (  # noqa: E402
    categoria_resumo,
    decimal_br,
    insights_gerais,
    mensal,
    numero,
    ranking,
    signed_percent,
    top_n_share,
    yoy_total,
)
from src.charts import (  # noqa: E402
    grafico_categoria_comparado,
    grafico_composicao_categorias,
    grafico_empresa_mix,
    grafico_empresa_periodo,
    grafico_evolucao_geral,
    grafico_pareto,
    grafico_ranking,
)
from src.config import CATEGORIAS, COLORS, Filters, MESES_ABREV, PLOT_CONFIG  # noqa: E402
from src.data import (  # noqa: E402
    anos_disponiveis,
    combinar,
    datasets,
    filtrar,
    ultimo_mes_disponivel,
    registros_para_exibicao,
)
from src.ui import chart_title, header, inject_css, insight_strip, metric_row, ranking_table_html  # noqa: E402


st.set_page_config(
    page_title="PB | Indicadores do Departamento Pessoal",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.session_state.setdefault("base_dir", BASE_DIR)
inject_css()


@st.cache_data(ttl=1800, max_entries=2, show_spinner=False)
def load_all() -> dict[str, object]:
    return datasets()


try:
    DFS = load_all()
except Exception as exc:
    st.error("Não foi possível carregar os dados do dashboard.")
    st.exception(exc)
    st.stop()

YEARS = anos_disponiveis(DFS)
if not YEARS:
    st.warning("Não existem anos de referência disponíveis.")
    st.stop()

LATEST_YEAR = YEARS[-1]
LATEST_MONTH = ultimo_mes_disponivel(DFS, LATEST_YEAR)


def init_filters() -> None:
    st.session_state.setdefault("filter_year", LATEST_YEAR)
    st.session_state.setdefault("filter_period", (1, LATEST_MONTH))
    st.session_state.setdefault("filter_categories", list(CATEGORIAS))

    # Corrige estados antigos ou anos removidos da base.
    if st.session_state["filter_year"] not in YEARS:
        st.session_state["filter_year"] = LATEST_YEAR
        st.session_state["filter_period"] = (1, LATEST_MONTH)

    start, end = st.session_state["filter_period"]
    max_month = ultimo_mes_disponivel(DFS, st.session_state["filter_year"])
    start = min(max(int(start), 1), max_month)
    end = min(max(int(end), start), max_month)
    st.session_state["filter_period"] = (start, end)


init_filters()


def active_filters() -> Filters:
    start, end = st.session_state["filter_period"]
    categories = tuple(st.session_state.get("filter_categories", CATEGORIAS))
    return Filters(
        year=int(st.session_state["filter_year"]),
        start_month=int(start),
        end_month=int(end),
        categories=categories or tuple(CATEGORIAS),
    )


def render_filter_bar(show_categories: bool = True) -> Filters:
    with st.container(border=True, key="filter_bar"):
        st.markdown('<div class="filterbar-title">Contexto de análise</div>', unsafe_allow_html=True)
        cols = st.columns([.85, 1.45, 2.2, 1.9], gap="small")
        with cols[0]:
            st.selectbox("Ano", YEARS, key="filter_year")
        with cols[1]:
            max_month = ultimo_mes_disponivel(DFS, int(st.session_state["filter_year"]))
            previous = st.session_state.get("filter_period", (1, max_month))
            previous = (min(previous[0], max_month), min(previous[1], max_month))
            if previous[0] > previous[1]:
                previous = (1, max_month)
            st.select_slider(
                "Período",
                options=list(range(1, max_month + 1)),
                value=previous,
                format_func=lambda x: MESES_ABREV[x],
                key="filter_period",
            )
        with cols[2]:
            if show_categories:
                st.multiselect("Categorias", CATEGORIAS, key="filter_categories", placeholder="Todas")
            else:
                st.markdown('<div class="filter-summary">Filtro global: ano + período</div>', unsafe_allow_html=True)
        with cols[3]:
            f = active_filters()
            st.markdown(
                f'<div class="filter-summary"><b>{f.period_label}</b><br>{len(f.categories)} categoria(s) • filtros preservados entre páginas</div>',
                unsafe_allow_html=True,
            )
    return active_filters()


def filtered_combined(f: Filters) -> object:
    combined = combinar({c: DFS[c] for c in f.categories}, f.categories)
    if combined.empty:
        return combined
    return filtrar(combined, f.year, f.start_month, f.end_month)


def page_overview() -> None:
    f = render_filter_bar(show_categories=True)
    base = filtered_combined(f)
    context = f"Dados disponíveis até {MESES_ABREV[ultimo_mes_disponivel(DFS, f.year)]} de {f.year}."
    header(
        "Cockpit executivo",
        "Departamento Pessoal",
        "Leitura consolidada do volume de trabalho, evolução e concentração das demandas.",
        context,
    )

    total = len(base)
    active_companies = int(base["empresa"].nunique()) if not base.empty else 0
    m = mensal(base, f.start_month, f.end_month)
    peak = int(m["volume"].max()) if not m.empty else 0
    peak_month = str(m.loc[m["volume"].idxmax(), "mes"]) if not m.empty and peak else "—"
    media = float(m["volume"].mean()) if not m.empty else 0
    yoy = yoy_total(DFS, f.categories, f.year, f.start_month, f.end_month)

    metric_row([
        ("Volume total", numero(total), signed_percent(yoy) if yoy is not None else None, "Variação contra o mesmo período do ano anterior."),
        ("Média mensal", decimal_br(media), None, "Média de movimentações nos meses do período selecionado."),
        ("Pico de demanda", numero(peak), None, f"{peak_month} foi o mês com maior volume no período." if peak else "Não há pico disponível."),
        ("Empresas atendidas", numero(active_companies), None, "Quantidade de empresas com pelo menos um registro."),
    ])

    insight_strip(insights_gerais(DFS, f.year, f.start_month, f.end_month, f.categories))

    c1, c2 = st.columns([1.62, 1], gap="large")
    with c1:
        chart_title("Evolução", "Volume mensal", "Barras mostram o volume observado; a linha suaviza a leitura da tendência recente.")
        st.plotly_chart(grafico_evolucao_geral(base, f.year, f.start_month, f.end_month), width="stretch", config=PLOT_CONFIG)
    with c2:
        chart_title("Composição", "Distribuição por categoria", "A composição evidencia o peso relativo de cada tipo de demanda.")
        st.plotly_chart(grafico_composicao_categorias(base, f.start_month, f.end_month), width="stretch", config=PLOT_CONFIG)
        mix = categoria_resumo({c: DFS[c] for c in f.categories}, f.year, f.start_month, f.end_month)
        st.dataframe(
            mix.rename(columns={"categoria": "Categoria", "volume": "Volume", "participacao": "Participação"}),
            width="stretch",
            hide_index=True,
            height=165,
            column_config={
                "Categoria": st.column_config.TextColumn(width="medium"),
                "Volume": st.column_config.NumberColumn(format="%d", width="small"),
                "Participação": st.column_config.NumberColumn(format="%.1f%%", width="small"),
            },
        )

    c3, c4 = st.columns([1.35, 1], gap="large")
    with c3:
        chart_title("Concentração", "Empresas com maior demanda", "O ranking responde diretamente onde está o maior volume de trabalho.")
        st.plotly_chart(grafico_ranking(base, 10), width="stretch", config=PLOT_CONFIG)
    with c4:
        chart_title("Dependência da carteira", "Pareto das maiores empresas", "A curva mostra quanto do volume já está coberto pelas maiores empresas.")
        st.plotly_chart(grafico_pareto(base, 10), width="stretch", config=PLOT_CONFIG)

    rank = ranking(base)
    if not rank.empty:
        st.markdown('<div class="section-note" style="margin-top:.2rem">Top 5 empresas concentram <b>{}</b> do volume selecionado.</div>'.format(percentual_br(top_n_share(base, 5))), unsafe_allow_html=True)
        with st.expander("Ver ranking completo"):
            st.markdown(ranking_table_html(rank, len(rank)), unsafe_allow_html=True)


def percentual_br(x: float) -> str:
    return f"{x:.1f}%".replace(".", ",")


def page_category(categoria: str) -> None:
    f = render_filter_bar(show_categories=False)
    df = filtrar(DFS[categoria], f.year, f.start_month, f.end_month)
    color = COLORS[categoria]
    context = f"{numero(len(df))} registros no período • {f.period_label}."
    header(
        categoria,
        f"{categoria}",
        f"Leitura operacional e gerencial da demanda de {categoria.lower()}.",
        context,
    )

    if df.empty:
        st.markdown('<div class="empty-state">Não há registros para os filtros selecionados.</div>', unsafe_allow_html=True)
        return

    m = mensal(df, f.start_month, f.end_month)
    total = len(df)
    media = float(m["volume"].mean())
    pico = int(m["volume"].max())
    mes_pico = str(m.loc[m["volume"].idxmax(), "mes"])
    empresas = int(df["empresa"].nunique())
    yoy = None
    prev = filtrar(DFS[categoria], f.year - 1, f.start_month, f.end_month)
    if not prev.empty or (DFS[categoria]["ano_referencia"] == f.year - 1).any():
        ant = len(prev)
        yoy = None if ant == 0 and total == 0 else (100.0 if ant == 0 else (total / ant - 1) * 100)

    metric_row([
        ("Volume", numero(total), signed_percent(yoy) if yoy is not None else None, "Variação contra o mesmo período do ano anterior."),
        ("Média mensal", decimal_br(media), None, "Média de registros por mês no período."),
        ("Pico", numero(pico), mes_pico, "Mês com maior demanda."),
        ("Empresas atendidas", numero(empresas), None, "Empresas que geraram pelo menos um registro."),
    ])

    c1, c2 = st.columns([1.45, .95], gap="large")
    with c1:
        chart_title("Evolução", f"{categoria}: trajetória mensal", "A linha tracejada representa o mesmo período do ano anterior quando disponível.")
        st.plotly_chart(grafico_categoria_comparado(DFS[categoria], f.year, f.start_month, f.end_month, color), width="stretch", config=PLOT_CONFIG)
    with c2:
        rank = ranking(df)
        chart_title("Concentração", "Empresas com maior demanda", "Volume e participação no período.")
        st.plotly_chart(grafico_ranking(df, 9, color), width="stretch", config=PLOT_CONFIG)

    c3, c4 = st.columns([1.1, .9], gap="large")
    with c3:
        chart_title("Ranking", "Distribuição por empresa")
        st.markdown(ranking_table_html(rank, 10), unsafe_allow_html=True)
    with c4:
        chart_title("Empresa em foco", "Perfil da empresa selecionada")
        if rank.empty:
            st.info("Sem empresas disponíveis.")
            return
        empresa = st.selectbox("Empresa", rank["empresa"].tolist(), key=f"company_focus_{categoria}_{f.year}", label_visibility="collapsed")
        df_emp = df[df["empresa"].eq(empresa)].copy()
        total_emp = len(df_emp)
        share = total_emp / total * 100 if total else 0
        mm = mensal(df_emp, f.start_month, f.end_month)
        peak_emp = int(mm["volume"].max()) if not mm.empty else 0
        a, b, c = st.columns(3, gap="small")
        a.metric("Volume", numero(total_emp))
        b.metric("Participação", f"{decimal_br(share)}%")
        c.metric("Pico", numero(peak_emp))
        st.plotly_chart(grafico_empresa_periodo(DFS[categoria], f.year, f.start_month, f.end_month, empresa, color), width="stretch", config=PLOT_CONFIG)

        with st.expander("Ver registros"):
            tabela = registros_para_exibicao(df_emp, categoria)
            if tabela.empty:
                st.info("Não foi possível localizar as colunas de detalhamento disponíveis na base.")
            else:
                col_cfg = {}
                for col in tabela.columns:
                    if col in ["Empresa", "Funcionário"]:
                        col_cfg[col] = st.column_config.TextColumn(width="medium")
                    elif col == "Ano":
                        col_cfg[col] = st.column_config.NumberColumn(format="%d", width="small")
                    else:
                        col_cfg[col] = st.column_config.TextColumn(width="small")
                st.dataframe(tabela, width="stretch", hide_index=True, height=360, column_config=col_cfg, lazy=True)


def page_companies() -> None:
    f = render_filter_bar(show_categories=True)
    base = filtered_combined(f)
    header(
        "Carteira",
        "Empresas",
        "Onde está a demanda e como o perfil de cada empresa se distribui entre as categorias.",
        f"Período analisado: {f.period_label}.",
    )
    if base.empty:
        st.markdown('<div class="empty-state">Não há empresas para os filtros selecionados.</div>', unsafe_allow_html=True)
        return

    rank = ranking(base)
    top = rank.iloc[0]
    metric_row([
        ("Empresas", numero(len(rank)), None, "Número de empresas com demanda no período."),
        ("Maior demandante", str(top["empresa"]), None, "Empresa com maior volume no período."),
        ("Volume da líder", numero(top["volume"]), None, f"A líder representa {decimal_br(top['participacao'])}% do volume total."),
        ("Top 5", percentual_br(top_n_share(base, 5)), None, "Participação acumulada das cinco maiores empresas."),
    ])

    c1, c2 = st.columns([1.15, 1], gap="large")
    with c1:
        chart_title("Ranking", "Maiores empresas por volume", "Use o ranking como ponto de entrada para investigar concentração e dependência da carteira.")
        st.plotly_chart(grafico_ranking(base, 14), width="stretch", config=PLOT_CONFIG)
    with c2:
        chart_title("Curva de concentração", "Pareto da carteira")
        st.plotly_chart(grafico_pareto(base, 14), width="stretch", config=PLOT_CONFIG)

    st.markdown("<div style='height:.2rem'></div>", unsafe_allow_html=True)
    c3, c4 = st.columns([1, 1], gap="large")
    with c3:
        chart_title("Empresa em foco", "Selecione uma empresa")
        empresas = rank["empresa"].tolist()
        empresa = st.selectbox("Empresa", empresas, key=f"empresa_carteira_{f.year}_{f.start_month}_{f.end_month}", label_visibility="collapsed")
        df_emp = base[base["empresa"].eq(empresa)].copy()
        total_emp = len(df_emp)
        share = total_emp / len(base) * 100 if len(base) else 0
        st.metric("Volume no período", numero(total_emp), f"{decimal_br(share)}% do total")
        st.plotly_chart(grafico_empresa_mix(df_emp), width="stretch", config=PLOT_CONFIG)
    with c4:
        chart_title("Evolução", "Volume mensal da empresa")
        st.plotly_chart(grafico_evolucao_geral(df_emp, f.year, f.start_month, f.end_month), width="stretch", config=PLOT_CONFIG)

    with st.expander("Ver ranking completo e participação"):
        st.dataframe(
            rank.rename(columns={"posicao": "Posição", "empresa": "Empresa", "volume": "Volume", "participacao": "Participação", "acumulado": "Acumulado"})[["Posição", "Empresa", "Volume", "Participação", "Acumulado"]],
            width="stretch",
            hide_index=True,
            height=420,
            column_config={
                "Posição": st.column_config.NumberColumn(format="%d", width="small"),
                "Empresa": st.column_config.TextColumn(width="large"),
                "Volume": st.column_config.NumberColumn(format="%d", width="small"),
                "Participação": st.column_config.NumberColumn(format="%.1f%%", width="small"),
                "Acumulado": st.column_config.NumberColumn(format="%.1f%%", width="small"),
            },
            lazy=True,
        )


PAGES = [
    st.Page(page_overview, title="Visão Geral", url_path="", default=True),
    st.Page(lambda: page_category("Admissões"), title="Admissões", url_path="admissoes"),
    st.Page(lambda: page_category("Férias"), title="Férias", url_path="ferias"),
    st.Page(lambda: page_category("Rescisões"), title="Rescisões", url_path="rescisoes"),
    st.Page(page_companies, title="Empresas", url_path="empresas"),
]

pg = st.navigation(PAGES, position="top")
pg.run()
