from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta
from plotly.subplots import make_subplots
import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Dashboard TechStore Brasil",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design tokens ─────────────────────────────────────────────────────────────
BG_MAIN    = "#0a0a0f"
BG_CARD    = "#1a1a24"
C_GREEN    = "#00d4aa"
C_BLUE     = "#4d9fff"
C_ORANGE   = "#ff8c42"
C_PURPLE   = "#b06cff"
C_RED      = "#ff4d6d"
C_TEXT     = "#e8e8f0"
C_MUTED    = "#8888a0"
C_BORDER   = "rgba(255,255,255,0.08)"

PALETTE = [C_BLUE, C_GREEN, C_ORANGE, C_PURPLE, "#ffd166", "#06d6a0", "#ef476f", "#118ab2"]

# ── CSS injection ─────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif !important;
    background-color: {BG_MAIN} !important;
    color: {C_TEXT} !important;
}}

/* Modern Streamlit selectors */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section[data-testid="stMain"] > div,
[data-testid="stHeader"] {{
    background-color: {BG_MAIN} !important;
}}
/* Ensure all text is visible */
p, span, label, div, h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdown"],
[data-testid="stWidgetLabel"],
.stRadio label, .stSelectbox label,
[data-baseweb="radio"] label,
[data-testid="stRadio"] label {{
    color: {C_TEXT} !important;
    font-family: 'Inter', sans-serif !important;
}}

.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1440px !important;
}}
#MainMenu, footer {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

.kpi-card {{
    background: {BG_CARD};
    border: 1px solid {C_BORDER};
    border-radius: 14px;
    padding: 20px 22px 16px;
    min-height: 124px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: transform .2s ease, box-shadow .2s ease;
}}
.kpi-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 10px 36px rgba(0,0,0,.45);
}}
.kpi-label {{
    font-size: .72rem;
    font-weight: 600;
    color: {C_MUTED};
    text-transform: uppercase;
    letter-spacing: .08em;
}}
.kpi-value {{
    font-size: 1.7rem;
    font-weight: 700;
    color: {C_TEXT};
    letter-spacing: -.03em;
    line-height: 1.15;
    margin: 6px 0 4px;
}}
.delta-pos  {{ font-size:.76rem; font-weight:600; color:{C_GREEN}; }}
.delta-neg  {{ font-size:.76rem; font-weight:600; color:{C_RED};   }}
.delta-neu  {{ font-size:.76rem; font-weight:600; color:{C_MUTED}; }}

.sec-title   {{ font-size:.95rem; font-weight:600; color:{C_TEXT}; letter-spacing:-.01em; }}
.sec-insight {{ font-size:.74rem; color:{C_MUTED}; margin-bottom:6px; }}

.sep {{ border:none; border-top:1px solid {C_BORDER}; margin:28px 0; }}

.dash-title    {{ font-size:1.85rem; font-weight:700; color:{C_TEXT}; letter-spacing:-.035em; }}
.dash-subtitle {{ font-size:.84rem; color:{C_MUTED}; margin-top:3px; }}
.dash-footer   {{ text-align:center; font-size:.71rem; color:{C_MUTED}; padding:36px 0 8px; }}

[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {{
    background-color:{BG_CARD} !important;
    border-right:1px solid {C_BORDER};
}}
[data-testid="stSidebar"] * {{
    color: {C_TEXT} !important;
}}

/* Restore Material Symbols font for sidebar collapse/expand buttons */
[data-testid="stSidebarCollapseButton"] span,
[data-testid="collapsedControl"] span {{
    font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    color: {C_TEXT} !important;
}}
</style>
""", unsafe_allow_html=True)


# ── Utilities ─────────────────────────────────────────────────────────────────
def fmt_brl(v: float) -> str:
    neg = v < 0
    v = abs(v)
    if v >= 1_000_000:
        s = f"{v / 1_000_000:.1f}M".replace(".", ",")
        return ("-R$ " if neg else "R$ ") + s
    s = f"{v:_.0f}".replace("_", ".")
    return ("-R$ " if neg else "R$ ") + s


def fmt_pct(v: float) -> str:
    return f"{v:.1f}%".replace(".", ",")


def fmt_num(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".")


def delta_html(cur: float, prev: float, invert: bool = False) -> str:
    if prev == 0:
        return '<span class="delta-neu">— sem período anterior</span>'
    pct = (cur - prev) / abs(prev) * 100
    good = (pct > 0) if not invert else (pct < 0)
    arrow = "▲" if pct > 0 else "▼"
    cls = "delta-pos" if good else "delta-neg"
    return f'<span class="{cls}">{arrow} {abs(pct):.1f}% vs. período anterior</span>'


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_excel("base_vendas_techstore.xlsx", engine="openpyxl")
    df["Data"] = pd.to_datetime(df["Data"])
    df["MesTS"] = df["Data"].dt.to_period("M").dt.to_timestamp()
    df["Margem"] = (df["Lucro"] / df["Valor_Total"] * 100).round(2)
    return df


def period_bounds(df: pd.DataFrame, periodo: str):
    dmax = df["Data"].max()
    dmin = df["Data"].min()
    if periodo == "6 meses":
        corte     = dmax - relativedelta(months=6)
        ant_fim   = corte
        ant_ini   = corte - relativedelta(months=6)
    elif periodo == "12 meses":
        corte     = dmax - relativedelta(months=12)
        ant_fim   = corte
        ant_ini   = corte - relativedelta(months=12)
    else:
        mid       = dmin + (dmax - dmin) / 2
        corte     = mid
        ant_fim   = mid
        ant_ini   = dmin
    return corte, dmax, ant_ini, ant_fim


def filter_data(df: pd.DataFrame, periodo: str):
    ini, fim, ant_ini, ant_fim = period_bounds(df, periodo)
    cur = df[(df["Data"] > ini)     & (df["Data"] <= fim)]
    ant = df[(df["Data"] > ant_ini) & (df["Data"] <= ant_fim)]
    return cur, ant


# ── Chart defaults ────────────────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color=C_TEXT, size=12),
    margin=dict(l=0, r=0, t=16, b=0),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=C_BORDER, font=dict(color=C_MUTED)),
)
_AXIS = dict(
    gridcolor="rgba(255,255,255,0.06)",
    linecolor="rgba(255,255,255,0.10)",
    tickfont=dict(color=C_MUTED),
)


def _apply(fig: go.Figure) -> go.Figure:
    fig.update_layout(**_LAYOUT, xaxis=_AXIS, yaxis=_AXIS)
    return fig


# ── KPI section ───────────────────────────────────────────────────────────────
def render_kpis(df: pd.DataFrame, df_ant: pd.DataFrame) -> None:
    receita  = df["Valor_Total"].sum()
    lucro    = df["Lucro"].sum()
    margem   = lucro / receita * 100 if receita else 0
    ticket   = df["Valor_Total"].mean()
    pedidos  = len(df)

    r_a = df_ant["Valor_Total"].sum()
    l_a = df_ant["Lucro"].sum()
    m_a = l_a / r_a * 100 if r_a else 0
    t_a = df_ant["Valor_Total"].mean() if len(df_ant) else 0
    p_a = len(df_ant)

    cards = [
        ("Receita Total",    fmt_brl(receita),  delta_html(receita, r_a)),
        ("Lucro Total",      fmt_brl(lucro),    delta_html(lucro, l_a)),
        ("Margem de Lucro",  fmt_pct(margem),   delta_html(margem, m_a)),
        ("Ticket Médio",     fmt_brl(ticket),   delta_html(ticket, t_a)),
        ("Total de Pedidos", fmt_num(pedidos),  delta_html(pedidos, p_a)),
    ]

    for col, (label, value, delta) in zip(st.columns(5), cards):
        col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta}
        </div>""", unsafe_allow_html=True)


# ── Individual charts ─────────────────────────────────────────────────────────
def g1_receita_lucro(df: pd.DataFrame) -> go.Figure:
    m = (df.groupby("MesTS")
           .agg(Receita=("Valor_Total", "sum"), Lucro=("Lucro", "sum"))
           .reset_index().sort_values("MesTS"))

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=m["MesTS"], y=m["Receita"], name="Receita",
        line=dict(color=C_BLUE, width=2.5),
        fill="tozeroy", fillcolor="rgba(77,159,255,0.10)",
        hovertemplate="<b>%{x|%b/%Y}</b><br>Receita: R$ %{y:,.0f}<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=m["MesTS"], y=m["Lucro"], name="Lucro",
        line=dict(color=C_GREEN, width=2.5),
        hovertemplate="<b>%{x|%b/%Y}</b><br>Lucro: R$ %{y:,.0f}<extra></extra>",
    ), secondary_y=True)

    axis_style = dict(**_AXIS, tickprefix="R$ ")
    fig.update_yaxes(secondary_y=False, **axis_style)
    fig.update_yaxes(secondary_y=True,  **axis_style)
    fig.update_xaxes(**_AXIS)
    base = {k: v for k, v in _LAYOUT.items() if k != "legend"}
    fig.update_layout(**base, legend=dict(
        orientation="h", y=1.08, x=0,
        bgcolor="rgba(0,0,0,0)", bordercolor=C_BORDER, font=dict(color=C_MUTED),
    ))
    return fig


def g2_categoria(df: pd.DataFrame) -> go.Figure:
    cat = (df.groupby("Categoria")["Valor_Total"].sum()
             .reset_index().sort_values("Valor_Total"))
    fig = px.bar(cat, x="Valor_Total", y="Categoria", orientation="h",
                 color="Categoria", color_discrete_sequence=PALETTE,
                 labels={"Valor_Total": "", "Categoria": ""})
    fig.update_traces(hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f}<extra></extra>")
    fig.update_layout(showlegend=False)
    return _apply(fig)


def g3_canal(df: pd.DataFrame) -> go.Figure:
    c = (df.groupby("Canal_Venda")["Valor_Total"].sum()
           .reset_index().sort_values("Valor_Total", ascending=False))
    fig = px.bar(c, x="Canal_Venda", y="Valor_Total",
                 color="Canal_Venda", color_discrete_sequence=PALETTE,
                 labels={"Valor_Total": "Receita (R$)", "Canal_Venda": ""})
    fig.update_traces(hovertemplate="<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>")
    fig.update_layout(showlegend=False)
    return _apply(fig)


def g4_regiao(df: pd.DataFrame) -> go.Figure:
    r = (df.groupby("Regiao")["Valor_Total"].sum()
           .reset_index().sort_values("Valor_Total"))
    fig = px.bar(r, x="Valor_Total", y="Regiao", orientation="h",
                 color="Regiao", color_discrete_sequence=PALETTE,
                 labels={"Valor_Total": "Receita (R$)", "Regiao": ""})
    fig.update_traces(hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f}<extra></extra>")
    fig.update_layout(showlegend=False)
    return _apply(fig)


def g5_top_produtos(df: pd.DataFrame) -> go.Figure:
    top = (df.groupby("Produto")["Valor_Total"].sum()
             .nlargest(10).reset_index().sort_values("Valor_Total"))
    fig = px.bar(top, x="Valor_Total", y="Produto", orientation="h",
                 color_discrete_sequence=[C_ORANGE],
                 labels={"Valor_Total": "Receita (R$)", "Produto": ""})
    fig.update_traces(hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f}<extra></extra>",
                      marker_color=C_ORANGE)
    return _apply(fig)


def g6_margem_tempo(df: pd.DataFrame) -> go.Figure:
    m = (df.groupby("MesTS")
           .apply(lambda x: x["Lucro"].sum() / x["Valor_Total"].sum() * 100, include_groups=False)
           .reset_index(name="Margem").sort_values("MesTS"))
    fig = px.area(m, x="MesTS", y="Margem",
                  color_discrete_sequence=[C_GREEN],
                  labels={"MesTS": "", "Margem": "Margem (%)"})
    fig.update_traces(
        hovertemplate="<b>%{x|%b/%Y}</b><br>Margem: %{y:.1f}%<extra></extra>",
        fillcolor="rgba(0,212,170,0.14)",
        line_color=C_GREEN,
    )
    return _apply(fig)


def g7_pagamento(df: pd.DataFrame) -> go.Figure:
    p = df.groupby("Forma_Pagamento")["Valor_Total"].sum().reset_index()
    fig = go.Figure(go.Pie(
        labels=p["Forma_Pagamento"],
        values=p["Valor_Total"],
        hole=0.55,
        marker=dict(colors=PALETTE, line=dict(color=BG_CARD, width=3)),
        hovertemplate="<b>%{label}</b><br>R$ %{value:,.0f}<br>%{percent}<extra></extra>",
        textfont=dict(color=C_TEXT, size=12),
    ))
    base = {k: v for k, v in _LAYOUT.items() if k != "legend"}
    fig.update_layout(**base, legend=dict(
        orientation="v", x=1, y=0.5,
        bgcolor="rgba(0,0,0,0)", bordercolor=C_BORDER, font=dict(color=C_MUTED),
    ))
    return fig


def g8_vendedores(df: pd.DataFrame) -> go.Figure:
    top5 = (df.groupby("Vendedor")["Valor_Total"].sum()
              .nlargest(5).reset_index().sort_values("Valor_Total"))
    fig = px.bar(top5, x="Valor_Total", y="Vendedor", orientation="h",
                 color="Valor_Total",
                 color_continuous_scale=[[0, C_BLUE], [1, C_GREEN]],
                 labels={"Valor_Total": "Receita (R$)", "Vendedor": ""})
    fig.update_traces(hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f}<extra></extra>")
    fig.update_layout(coloraxis_showscale=False)
    return _apply(fig)


# ── Monthly table ─────────────────────────────────────────────────────────────
def render_tabela(df: pd.DataFrame) -> None:
    m = (df.groupby("MesTS")
           .agg(Receita=("Valor_Total", "sum"),
                Custo=("Custo_Total", "sum"),
                Lucro=("Lucro", "sum"))
           .reset_index().sort_values("MesTS"))
    m["Margem (%)"] = (m["Lucro"] / m["Receita"] * 100).round(1)
    m["Mês"] = m["MesTS"].dt.strftime("%b/%Y")
    display = m[["Mês", "Receita", "Custo", "Lucro", "Margem (%)"]].copy()
    for col in ["Receita", "Custo", "Lucro"]:
        display[col] = display[col].apply(fmt_brl)
    display["Margem (%)"] = display["Margem (%)"].apply(fmt_pct)
    st.dataframe(display.set_index("Mês"), use_container_width=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    df_full = load_data()

    with st.sidebar:
        st.markdown(
            f"<div style='color:{C_MUTED};font-size:.72rem;font-weight:600;"
            f"text-transform:uppercase;letter-spacing:.08em;padding:16px 0 10px'>"
            f"Filtros</div>",
            unsafe_allow_html=True,
        )
        periodo = st.radio("Período de análise", ["6 meses", "12 meses", "Tudo"], index=2)
        st.markdown(
            f"<div style='color:{C_MUTED};font-size:.72rem;margin-top:20px'>"
            f"Base: {df_full['Data'].min().strftime('%b/%Y')} → "
            f"{df_full['Data'].max().strftime('%b/%Y')}<br>"
            f"{fmt_num(len(df_full))} transações</div>",
            unsafe_allow_html=True,
        )

    df, df_ant = filter_data(df_full, periodo)

    label_periodo = (
        f"{df['Data'].min().strftime('%b/%Y')} – {df['Data'].max().strftime('%b/%Y')}"
        if len(df) else "—"
    )

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="padding:10px 0 24px">
        <div class="dash-title">📊 Dashboard TechStore Brasil</div>
        <div class="dash-subtitle">
            Período: {label_periodo} &nbsp;·&nbsp;
            {fmt_num(len(df))} pedidos &nbsp;·&nbsp;
            Última transação: {df_full['Data'].max().strftime('%d/%m/%Y')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    render_kpis(df, df_ant)

    st.markdown("<hr class='sep'>", unsafe_allow_html=True)

    # ── G1 + G2 ───────────────────────────────────────────────────────────────
    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        melhor = df.groupby("MesTS")["Valor_Total"].sum().idxmax() if len(df) else None
        insight = melhor.strftime("%b/%Y") if melhor is not None else "—"
        st.markdown(f'<div class="sec-title">Evolução Mensal — Receita vs. Lucro</div>'
                    f'<div class="sec-insight">Melhor mês em receita: {insight}</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(g1_receita_lucro(df), use_container_width=True)
    with c2:
        top_cat = df.groupby("Categoria")["Valor_Total"].sum().idxmax() if len(df) else "—"
        st.markdown(f'<div class="sec-title">Receita por Categoria</div>'
                    f'<div class="sec-insight">Maior categoria: {top_cat}</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(g2_categoria(df), use_container_width=True)

    # ── G3 + G4 ───────────────────────────────────────────────────────────────
    c3, c4 = st.columns(2, gap="large")
    with c3:
        top_canal = df.groupby("Canal_Venda")["Valor_Total"].sum().idxmax() if len(df) else "—"
        st.markdown(f'<div class="sec-title">Receita por Canal de Venda</div>'
                    f'<div class="sec-insight">Canal líder: {top_canal}</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(g3_canal(df), use_container_width=True)
    with c4:
        top_reg = df.groupby("Regiao")["Valor_Total"].sum().idxmax() if len(df) else "—"
        st.markdown(f'<div class="sec-title">Receita por Região</div>'
                    f'<div class="sec-insight">Região líder: {top_reg}</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(g4_regiao(df), use_container_width=True)

    # ── G5 full width ─────────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Top 10 Produtos — Receita Total</div>'
                '<div class="sec-insight">Produtos com maior faturamento no período selecionado</div>',
                unsafe_allow_html=True)
    st.plotly_chart(g5_top_produtos(df), use_container_width=True)

    # ── G6 + G7 ───────────────────────────────────────────────────────────────
    c5, c6 = st.columns([3, 2], gap="large")
    with c5:
        margem_media = df["Lucro"].sum() / df["Valor_Total"].sum() * 100 if len(df) else 0
        st.markdown(f'<div class="sec-title">Evolução da Margem de Lucro</div>'
                    f'<div class="sec-insight">Média no período: {fmt_pct(margem_media)}</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(g6_margem_tempo(df), use_container_width=True)
    with c6:
        st.markdown('<div class="sec-title">Vendas por Forma de Pagamento</div>'
                    '<div class="sec-insight">Distribuição de métodos no período</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(g7_pagamento(df), use_container_width=True)

    # ── G8 ────────────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Ranking de Vendedores — Top 5</div>'
                '<div class="sec-insight">Por receita total gerada no período selecionado</div>',
                unsafe_allow_html=True)
    st.plotly_chart(g8_vendedores(df), use_container_width=True)

    st.markdown("<hr class='sep'>", unsafe_allow_html=True)

    # ── Monthly table ─────────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Resumo Mensal Detalhado</div>'
                '<div class="sec-insight">Receita, Custo, Lucro e Margem por mês</div>',
                unsafe_allow_html=True)
    render_tabela(df)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="dash-footer">Dados fictícios — gerado em '
        f'{datetime.now().strftime("%d/%m/%Y")}</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
