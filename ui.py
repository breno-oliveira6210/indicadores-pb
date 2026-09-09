from __future__ import annotations

import html

import streamlit as st

from .config import COLORS, CATEGORIAS, MESES_ABREV
from .analytics import decimal_br, numero, signed_percent


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --bg: {COLORS['bg']};
            --surface: {COLORS['surface']};
            --text: {COLORS['text']};
            --muted: {COLORS['muted']};
            --border: {COLORS['border']};
        }}

        .stApp {{ background: var(--bg); }}
        section[data-testid="stSidebar"] {{ display: none !important; }}
        [data-testid="stSidebarCollapseButton"] {{ display: none !important; }}
        header[data-testid="stHeader"] {{
            background: rgba(255,255,255,.96) !important;
            border-bottom: 1px solid var(--border) !important;
        }}
        header[data-testid="stHeader"] > div:first-child {{ background: transparent !important; }}

        .block-container {{
            max-width: 1560px;
            padding: 4.75rem 3.2rem 3rem !important;
        }}

        @media (max-width: 1100px) {{
            .block-container {{ padding-left: 1.35rem !important; padding-right: 1.35rem !important; }}
        }}

        @media (max-width: 640px) {{
            .block-container {{ padding-top: 4.35rem !important; padding-left: .8rem !important; padding-right: .8rem !important; }}
        }}

        /* Top navigation: use native navigation, visually treated as a product navbar. */
        [data-testid="stHeader"] [data-testid="stNavigation"] {{
            width: 100%;
        }}
        [data-testid="stHeader"] nav {{
            border-bottom: none !important;
            box-shadow: none !important;
            justify-content: center;
        }}
        [data-testid="stHeader"] nav a {{
            color: #56616C !important;
            font-size: .86rem !important;
            font-weight: 650 !important;
            border-radius: 0 !important;
            padding: .72rem 1rem !important;
        }}
        [data-testid="stHeader"] nav a[aria-current="page"] {{
            color: #20262E !important;
            box-shadow: inset 0 -2px 0 #34404B !important;
        }}

        h1, h2, h3 {{
            color: var(--text) !important;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            letter-spacing: -0.028em;
        }}
        h1 {{ font-size: 2.0rem !important; margin: 0 0 .18rem !important; }}
        h2 {{ font-size: 1.23rem !important; margin: 0 !important; }}
        h3 {{ font-size: 1.0rem !important; }}

        .product-header {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 2rem;
            margin-bottom: 1.15rem;
        }}
        .brand {{ display: flex; align-items: center; gap: .8rem; }}
        .brand img {{ height: 34px; width: auto; object-fit: contain; }}
        .brand-name {{ color: #25303A; font-size: .86rem; font-weight: 800; letter-spacing: .02em; }}
        .brand-sub {{ color: var(--muted); font-size: .75rem; margin-top: .08rem; }}
        .eyebrow {{ color: var(--muted); font-size: .72rem; font-weight: 800; letter-spacing: .105em; text-transform: uppercase; margin-bottom: .35rem; }}
        .subtitle {{ color: var(--muted); font-size: .93rem; line-height: 1.45; margin: 0; max-width: 860px; }}
        .context {{ color: var(--muted); font-size: .78rem; margin-top: .38rem; }}
        .section-label {{ color: #5A6570; font-size: .73rem; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; margin-bottom: .28rem; }}
        .section-note {{ color: var(--muted); font-size: .77rem; margin-top: .15rem; }}

        .filterbar-title {{ color: #4E5964; font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; margin: .05rem 0 .42rem; }}
        .filter-summary {{ color: var(--muted); font-size: .73rem; padding-top: .3rem; white-space: nowrap; }}
        div[data-baseweb="select"] > div {{ border-color: var(--border) !important; border-radius: 8px !important; background: var(--surface) !important; min-height: 38px; }}
        div[data-baseweb="select"] > div:hover {{ border-color: #B7C0C8 !important; }}
        label[data-testid="stWidgetLabel"] p {{ color: #5F6A75 !important; font-size: .74rem !important; font-weight: 700 !important; }}

        /* Metrics: restrained cards, not a wall of tiles. */
        div[data-testid="stMetric"] {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 11px;
            padding: .82rem .95rem;
            min-height: 92px;
        }}
        div[data-testid="stMetricLabel"] p {{ color: var(--muted) !important; font-size: .76rem !important; font-weight: 700 !important; }}
        div[data-testid="stMetricValue"] {{ color: var(--text) !important; font-size: 1.62rem !important; letter-spacing: -.03em; }}
        div[data-testid="stMetricDelta"] svg {{ display: none; }}
        div[data-testid="stMetricDelta"] {{ font-size: .73rem !important; }}

        .insights {{ display: flex; gap: .65rem; flex-wrap: wrap; margin: .15rem 0 1.35rem; }}
        .insight {{ background: var(--surface); border: 1px solid var(--border); border-radius: 9px; padding: .65rem .75rem; min-width: 210px; flex: 1 1 210px; }}
        .insight-label {{ color: #59636E; font-size: .66rem; font-weight: 800; letter-spacing: .075em; text-transform: uppercase; margin-bottom: .2rem; }}
        .insight-text {{ color: var(--text); font-size: .80rem; line-height: 1.38; }}

        .chart-shell {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: .52rem .78rem .55rem; }}
        .chart-shell .section-label {{ padding: .22rem .2rem 0; }}

        .rank-table {{ width: 100%; border-collapse: collapse; font-size: .79rem; }}
        .rank-table th {{ text-align: left; color: #68737E; font-size: .67rem; text-transform: uppercase; letter-spacing: .06em; padding: .55rem .25rem; border-bottom: 1px solid var(--border); }}
        .rank-table td {{ padding: .55rem .25rem; border-bottom: 1px solid #EDF0F2; color: var(--text); }}
        .rank-table td:last-child, .rank-table th:last-child {{ text-align: right; }}
        .rank-table td:nth-child(3), .rank-table th:nth-child(3) {{ text-align: right; }}
        .rank-number {{ color: #8A949E; font-variant-numeric: tabular-nums; }}
        .share-pill {{ color: #505B66; font-variant-numeric: tabular-nums; }}

        .empty-state {{ background: var(--surface); border: 1px dashed #CBD3D9; border-radius: 12px; padding: 1.4rem; color: var(--muted); font-size: .86rem; }}
        .source-note {{ color: #7A858F; font-size: .7rem; line-height: 1.4; margin-top: .7rem; }}
        details[data-testid="stExpander"] {{ border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }}
        [data-testid="stDataFrame"] {{ border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }}
        #MainMenu, footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def header(eyebrow: str, title: str, subtitle: str, context: str | None = None) -> None:
    logo = (st.session_state.get("base_dir") and st.session_state["base_dir"] / "pb_logo.png")
    logo_html = ""
    if logo and logo.exists():
        # st.image seria mais robusto para alt text, porém o cabeçalho aqui é apenas
        # marca visual; caso o arquivo não exista, o sistema continua sem ele.
        logo_html = f'<img src="data:image/png;base64,{_read_b64(logo)}" alt="PB" />'
    st.markdown(
        f"""
        <div class="product-header">
          <div>
            <div class="eyebrow">{html.escape(eyebrow)}</div>
            <h1>{html.escape(title)}</h1>
            <p class="subtitle">{html.escape(subtitle)}</p>
            {f'<div class="context">{html.escape(context)}</div>' if context else ''}
          </div>
          {f'<div class="brand"><div>{logo_html}</div><div><div class="brand-name">PB Contabilidade Integrada</div><div class="brand-sub">Departamento Pessoal</div></div></div>' if logo_html else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _read_b64(path) -> str:
    import base64
    return base64.b64encode(path.read_bytes()).decode("ascii")


def metric_row(metrics: list[tuple[str, str, str | None, str | None]]) -> None:
    cols = st.columns(len(metrics), gap="small")
    for col, (label, value, delta, help_text) in zip(cols, metrics):
        with col:
            st.metric(label, value, delta=delta, help=help_text)


def insight_strip(items: list[dict[str, str]]) -> None:
    if not items:
        return
    content = "".join(
        f'<div class="insight"><div class="insight-label">{html.escape(i["label"])}</div><div class="insight-text">{html.escape(i["text"])}</div></div>'
        for i in items
    )
    st.markdown(f'<div class="insights">{content}</div>', unsafe_allow_html=True)


def chart_title(label: str, title: str, note: str | None = None) -> None:
    st.markdown(f'<div class="section-label">{html.escape(label)}</div>', unsafe_allow_html=True)
    st.markdown(f'<h2 style="margin-bottom:.1rem">{html.escape(title)}</h2>', unsafe_allow_html=True)
    if note:
        st.markdown(f'<div class="section-note">{html.escape(note)}</div>', unsafe_allow_html=True)


def ranking_table_html(rank, max_rows: int = 8) -> str:
    top = rank.head(max_rows)
    rows = "".join(
        f'<tr><td class="rank-number">{int(r.posicao)}</td><td>{html.escape(str(r.empresa))}</td><td>{numero(r.volume)}</td><td class="share-pill">{decimal_br(r.participacao)}%</td></tr>'
        for r in top.itertuples()
    )
    return f'<table class="rank-table"><thead><tr><th>#</th><th>Empresa</th><th>Volume</th><th>Part.</th></tr></thead><tbody>{rows}</tbody></table>'
