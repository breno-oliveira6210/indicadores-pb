from __future__ import annotations

from pathlib import Path
import sys
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.analytics import decimal_br, mensal, numero, percentual, ranking, resumo
from src.charts import (
    grafico_categoria_mensal,
    grafico_composicao,
    grafico_empresa_mensal,
    grafico_ranking,
    grafico_total_mensal,
)
from src.config import CATEGORIAS, COLORS, MESES_ABREV
from src.data import anos_disponiveis, carregar_dados, combinar, filtrar, registros_para_exibicao

st.set_page_config(
    page_title="PB | Departamento Pessoal",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data(ttl=1800, max_entries=2, show_spinner=False)
def load_data():
    return carregar_dados()


try:
    _adm, _fer, _res = load_data()
except Exception as exc:
    st.error("Não foi possível carregar os dados do dashboard.")
    st.exception(exc)
    st.stop()

DFS = {"Admissões": _adm, "Férias": _fer, "Rescisões": _res}
YEARS = anos_disponiveis(DFS)
if not YEARS:
    st.warning("Não existem anos de referência disponíveis.")
    st.stop()

LATEST_YEAR = YEARS[-1]


# -----------------------------------------------------------------------------
# CSS — visual propositalmente discreto
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --bg: #f6f7f8;
        --surface: #ffffff;
        --text: #22272e;
        --muted: #6d7680;
        --line: #dfe4e8;
        --line-soft: #e9edf0;
        --nav: #26313a;
    }

    .stApp { background: var(--bg); }
    .block-container {
        max-width: 1500px;
        padding: 1.25rem 2.5rem 3rem !important;
    }

    /* Sidebar: inexistente visualmente. */
    section[data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* Navegação nativa superior: forte e evidente. */
    header[data-testid="stHeader"] {
        background: #ffffff !important;
        border-bottom: 1px solid var(--line) !important;
        box-shadow: none !important;
    }
    [data-testid="stNavigation"] nav {
        justify-content: flex-start !important;
        gap: .15rem !important;
        padding: .25rem 1.3rem !important;
    }
    [data-testid="stNavigation"] a {
        color: #59636d !important;
        font-size: .88rem !important;
        font-weight: 700 !important;
        padding: .62rem .95rem !important;
        border-radius: 7px !important;
    }
    [data-testid="stNavigation"] a:hover {
        background: #f0f3f5 !important;
        color: #20272d !important;
    }
    [data-testid="stNavigation"] a[aria-current="page"] {
        background: var(--nav) !important;
        color: #ffffff !important;
    }

    h1, h2, h3 {
        color: var(--text) !important;
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        letter-spacing: -.025em;
    }
    h1 { font-size: 1.85rem !important; margin: 0 !important; }
    h2 { font-size: 1.12rem !important; margin: 0 !important; }

    .top-brand {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap: 1rem;
        margin: .25rem 0 1rem;
        padding-bottom: .85rem;
        border-bottom: 1px solid var(--line);
    }
    .brand-left { display:flex; align-items:center; gap:.7rem; }
    .brand-mark {
        width: 34px; height:34px; border-radius:8px;
        display:flex; align-items:center; justify-content:center;
        background:#25313a; color:#fff; font-size:.72rem; font-weight:800;
    }
    .brand-title { font-weight:800; color:#263039; font-size:.92rem; }
    .brand-sub { font-size:.72rem; color:var(--muted); margin-top:.1rem; }
    .data-context { font-size:.75rem; color:var(--muted); }

    .filter-strip {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 9px;
        padding: .65rem .8rem .7rem;
        margin-bottom: 1.35rem;
    }
    .filter-label {
        font-size: .68rem; font-weight:800; text-transform:uppercase;
        letter-spacing:.08em; color:#707983; margin-bottom:.45rem;
    }
    label[data-testid="stWidgetLabel"] p {
        font-size: .72rem !important;
        color: #65707a !important;
        font-weight: 700 !important;
    }
    div[data-baseweb="select"] > div {
        min-height:36px !important;
        border: 1px solid var(--line) !important;
        border-radius:7px !important;
    }

    .section-head {
        display:flex; align-items:baseline; justify-content:space-between;
        gap:1rem; margin: .2rem 0 .65rem;
    }
    .section-kicker {
        color:#77818a; font-size:.66rem; font-weight:800;
        text-transform:uppercase; letter-spacing:.1em;
    }
    .section-note { color:var(--muted); font-size:.74rem; }

    /* KPIs sem excesso de cartões. */
    div[data-testid="stMetric"] {
        background: transparent !important;
        border: 0 !important;
        border-radius: 0 !important;
        padding: .15rem .7rem .4rem .05rem !important;
        min-height: 0 !important;
        box-shadow:none !important;
    }
    div[data-testid="stMetricLabel"] p {
        color:#747d86 !important;
        font-size:.72rem !important;
        font-weight:700 !important;
    }
    div[data-testid="stMetricValue"] {
        color:var(--text) !important;
        font-size:1.55rem !important;
        letter-spacing:-.035em;
    }
    div[data-testid="stMetricDelta"] { font-size:.7rem !important; }
    div[data-testid="stMetricDelta"] svg { display:none !important; }

    .chart-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 9px;
        padding: .55rem .75rem .5rem;
    }
    .empty {
        background:#fff; border:1px dashed #cbd2d7; border-radius:9px;
        padding:1.4rem; color:var(--muted); font-size:.82rem;
    }
    .table-wrap { margin-top:.9rem; }
    [data-testid="stDataFrame"] {
        border:1px solid var(--line) !important;
        border-radius:8px !important;
        overflow:hidden;
    }
    details[data-testid="stExpander"] {
        border:1px solid var(--line) !important;
        border-radius:8px !important;
        background:#fff !important;
    }
    .caption {
        color:#7a838b; font-size:.68rem; margin-top:.4rem;
    }
    #MainMenu, footer { visibility:hidden; }

    @media (max-width: 900px) {
        .block-container { padding-left:1rem !important; padding-right:1rem !important; }
        [data-testid="stNavigation"] nav { overflow-x:auto !important; justify-content:flex-start !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def page_filters(allow_company: bool = False):
    max_month = 12
    start_default = 1
    end_default = 12

    st.markdown('<div class="filter-label">Filtros</div>', unsafe_allow_html=True)
    cols = st.columns([.85, 1.4, 1.8] if allow_company else [.9, 1.5], gap="small")
    with cols[0]:
        year = st.selectbox("Ano", YEARS, index=len(YEARS) - 1, key=f"year_{allow_company}")
    with cols[1]:
        period = st.select_slider(
            "Período",
            options=list(range(1, max_month + 1)),
            value=(start_default, end_default),
            format_func=lambda x: MESES_ABREV[x],
            key=f"period_{allow_company}",
        )
    company = None
    if allow_company:
        with cols[2]:
            all_companies = (
                pd.concat([DFS[c]["empresa"] for c in CATEGORIAS], ignore_index=True)
                .dropna().astype(str).str.strip().drop_duplicates().sort_values().tolist()
            )
            company = st.selectbox("Empresa", ["Todas as empresas", *all_companies], key="company_global")
    return int(year), int(period[0]), int(period[1]), company


def brand():
    logo = BASE_DIR / "pb_logo.png"
    if logo.exists():
        import base64
        b64 = base64.b64encode(logo.read_bytes()).decode("ascii")
        mark = f'<img src="data:image/png;base64,{b64}" style="height:32px;width:auto;object-fit:contain;" />'
    else:
        mark = '<div class="brand-mark">PB</div>'
    st.markdown(
        f'''<div class="top-brand"><div class="brand-left">{mark}<div><div class="brand-title">Departamento Pessoal</div><div class="brand-sub">PB Contabilidade Integrada</div></div></div><div class="data-context">Dados consolidados automaticamente</div></div>''',
        unsafe_allow_html=True,
    )


def section(kicker: str, title: str, note: str = ""):
    note_html = f'<div class="section-note">{note}</div>' if note else ''
    st.markdown(f'<div class="section-head"><div><div class="section-kicker">{kicker}</div><h2>{title}</h2></div>{note_html}</div>', unsafe_allow_html=True)


def render_kpis(items):
    cols = st.columns(len(items), gap="medium")
    for col, (label, value) in zip(cols, items):
        with col:
            st.metric(label, value)


def base_filtered(year, start, end):
    frames = []
    for cat in CATEGORIAS:
        df = filtrar(DFS[cat], year, start, end)
        if not df.empty:
            x = df.copy()
            x["categoria"] = cat
            frames.append(x)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def page_overview():
    brand()
    year, start, end, _ = page_filters()
    base = base_filtered(year, start, end)
    period = f"{MESES_ABREV[start]}–{MESES_ABREV[end]} {year}" if start != end else f"{MESES_ABREV[start]} {year}"

    section("Visão geral", "Movimentação do Departamento Pessoal", period)
    r = resumo(base, start, end) if not base.empty else {"total":0,"media":0,"pico":0,"mes_pico":"—","empresas":0}
    render_kpis([
        ("Volume total", numero(r["total"])),
        ("Média mensal", decimal_br(r["media"])),
        ("Maior mês", f'{numero(r["pico"])} · {r["mes_pico"]}' if r["pico"] else "—"),
        ("Empresas", numero(r["empresas"])),
    ])

    if base.empty:
        st.markdown('<div class="empty">Não há registros para os filtros selecionados.</div>', unsafe_allow_html=True)
        return

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
    section("Evolução", "Volume mensal")
    with st.container(border=True):
        st.plotly_chart(grafico_total_mensal(base, start, end), width="stretch", config={"displayModeBar":False,"responsive":True})

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.35], gap="large")
    with c1:
        section("Categorias", "Distribuição do volume")
        with st.container(border=True):
            st.plotly_chart(grafico_composicao(base, start, end), width="stretch", config={"displayModeBar":False,"responsive":True})
    with c2:
        section("Empresas", "Maiores volumes")
        with st.container(border=True):
            st.plotly_chart(grafico_ranking(base, 10), width="stretch", config={"displayModeBar":False,"responsive":True})

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    with st.expander("Ver ranking completo"):
        rank = ranking(base)
        if rank.empty:
            st.info("Sem registros.")
        else:
            table = rank[["posicao","empresa","volume","participacao"]].rename(columns={"posicao":"Posição","empresa":"Empresa","volume":"Volume","participacao":"Participação"})
            st.dataframe(table, width="stretch", hide_index=True, column_config={"Volume":st.column_config.NumberColumn(format="%d"),"Participação":st.column_config.NumberColumn(format="%.1f%%")}, height=420)


def page_category(categoria: str):
    brand()
    year, start, end, _ = page_filters()
    df = filtrar(DFS[categoria], year, start, end)
    period = f"{MESES_ABREV[start]}–{MESES_ABREV[end]} {year}" if start != end else f"{MESES_ABREV[start]} {year}"
    section(categoria, categoria, period)

    if df.empty:
        st.markdown('<div class="empty">Não há registros para os filtros selecionados.</div>', unsafe_allow_html=True)
        return

    r = resumo(df, start, end)
    render_kpis([
        ("Volume", numero(r["total"])),
        ("Média mensal", decimal_br(r["media"])),
        ("Maior mês", f'{numero(r["pico"])} · {r["mes_pico"]}'),
        ("Empresas", numero(r["empresas"])),
    ])

    st.markdown("<div style='height:.45rem'></div>", unsafe_allow_html=True)
    section("Evolução", "Volume mensal")
    with st.container(border=True):
        st.plotly_chart(grafico_categoria_mensal(df, categoria, start, end), width="stretch", config={"displayModeBar":False,"responsive":True})

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    section("Empresas", "Maiores volumes")
    with st.container(border=True):
        st.plotly_chart(grafico_ranking(df, 15, color=COLORS[categoria]), width="stretch", config={"displayModeBar":False,"responsive":True})

    rank = ranking(df)
    empresas = rank["empresa"].tolist()
    if not empresas:
        return

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    with st.expander("Analisar uma empresa"):
        empresa = st.selectbox("Empresa", empresas, key=f"empresa_{categoria}_{year}_{start}_{end}")
        df_emp = df[df["empresa"].eq(empresa)].copy()
        er = resumo(df_emp, start, end)
        a,b,c = st.columns(3)
        a.metric("Volume", numero(er["total"]))
        b.metric("Participação", percentual((er["total"] / r["total"] * 100) if r["total"] else 0))
        c.metric("Maior mês", f'{numero(er["pico"])} · {er["mes_pico"]}')
        st.plotly_chart(grafico_empresa_mensal(df_emp, start, end, color=COLORS[categoria]), width="stretch", config={"displayModeBar":False,"responsive":True})
        tabela = registros_para_exibicao(df_emp, categoria)
        if not tabela.empty:
            st.dataframe(tabela, width="stretch", hide_index=True, height=300)


def page_companies():
    brand()
    year, start, end, company = page_filters(allow_company=True)
    base = base_filtered(year, start, end)
    period = f"{MESES_ABREV[start]}–{MESES_ABREV[end]} {year}" if start != end else f"{MESES_ABREV[start]} {year}"
    section("Empresas", "Análise por empresa", period)

    if base.empty:
        st.markdown('<div class="empty">Não há registros para os filtros selecionados.</div>', unsafe_allow_html=True)
        return

    rank = ranking(base)
    if company == "Todas as empresas" or company is None:
        render_kpis([
            ("Empresas atendidas", numero(len(rank))),
            ("Volume total", numero(len(base))),
            ("Maior empresa", rank.iloc[0]["empresa"] if not rank.empty else "—"),
            ("Volume da maior", numero(int(rank.iloc[0]["volume"])) if not rank.empty else "—"),
        ])
        st.markdown("<div style='height:.45rem'></div>")
        section("Ranking", "Empresas por volume")
        with st.container(border=True):
            st.plotly_chart(grafico_ranking(base, 20), width="stretch", config={"displayModeBar":False,"responsive":True})
    else:
        df_emp = base[base["empresa"].eq(company)].copy()
        r = resumo(df_emp, start, end)
        total_base = len(base)
        render_kpis([
            ("Empresa", company),
            ("Volume", numero(r["total"])),
            ("Participação", percentual(r["total"] / total_base * 100 if total_base else 0)),
            ("Maior mês", f'{numero(r["pico"])} · {r["mes_pico"]}' if r["pico"] else "—"),
        ])
        st.markdown("<div style='height:.45rem'></div>")
        c1,c2 = st.columns([1.35, 1], gap="large")
        with c1:
            section("Evolução", "Volume mensal")
            with st.container(border=True):
                st.plotly_chart(grafico_empresa_mensal(df_emp, start, end), width="stretch", config={"displayModeBar":False,"responsive":True})
        with c2:
            section("Categoria", "Distribuição")
            with st.container(border=True):
                st.plotly_chart(grafico_composicao(df_emp, start, end), width="stretch", config={"displayModeBar":False,"responsive":True})
        tabela = registros_para_exibicao(df_emp, None) if False else None
        with st.expander("Ver registros"):
            for categoria in CATEGORIAS:
                x = df_emp[df_emp["categoria"].eq(categoria)]
                if not x.empty:
                    st.markdown(f"**{categoria}** — {len(x):,}".replace(",", "."))
                    t = registros_para_exibicao(x, categoria)
                    if not t.empty:
                        st.dataframe(t, width="stretch", hide_index=True, height=260)


def run():
    page = st.navigation(
        [
            st.Page(page_overview, title="Visão geral"),
            st.Page(lambda: page_category("Admissões"), title="Admissões"),
            st.Page(lambda: page_category("Férias"), title="Férias"),
            st.Page(lambda: page_category("Rescisões"), title="Rescisões"),
            st.Page(page_companies, title="Empresas"),
        ],
        position="top",
    )
    page.run()


if __name__ == "__main__":
    run()
