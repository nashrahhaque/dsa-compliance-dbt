"""
DSA Compliance Intelligence Dashboard
Swiss International Typographic Style
"""

import duckdb
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

DB_PATH = "dev.duckdb"

# ── Design tokens ─────────────────────────────────────────────────────────────
T = {
    "bg":          "#F7F6F3",
    "surface":     "#EFEDE9",
    "rule":        "#D8D5CF",
    "rule_light":  "#E8E5DF",
    "ink":         "#0D0D0D",
    "ink_2":       "#2D2D2D",
    "ink_3":       "#5A5A5A",
    "ink_4":       "#909090",
    "red":         "#A81C1C",
    "cobalt":      "#1B3D6B",
    "amber":       "#7A5C00",
    "green_ink":   "#1A4A2E",
    "mono":        "'JetBrains Mono', 'SF Mono', 'Fira Mono', monospace",
    "sans":        "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Arial, sans-serif",
}

st.set_page_config(
    page_title="DSA Compliance Intelligence",
    page_icon="◼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(f"""
<style>
/* ── Reset & base ─────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, .stApp {{
    background-color: {T['bg']} !important;
    color: {T['ink']};
    font-family: {T['sans']};
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

.main .block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

section[data-testid="stSidebar"] {{ display: none !important; }}

/* ── Streamlit chrome removal ─────────────────────────────── */
header[data-testid="stHeader"] {{ display: none; }}
div[data-testid="stToolbar"] {{ display: none; }}
#MainMenu {{ display: none; }}
footer {{ display: none; }}
div[data-testid="stDecoration"] {{ display: none; }}
div[data-testid="stMetric"] {{ display: none !important; }}

/* ── Grid wrapper ─────────────────────────────────────────── */
.ci-wrapper {{
    max-width: 1440px;
    margin: 0 auto;
    padding: 0 64px;
}}

@media (max-width: 900px) {{
    .ci-wrapper {{ padding: 0 24px; }}
}}

/* ── Masthead ─────────────────────────────────────────────── */
.masthead {{
    padding: 72px 0 0 0;
    border-bottom: 1px solid {T['rule']};
    margin-bottom: 0;
}}

.masthead-grid {{
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: end;
    gap: 40px;
    padding-bottom: 48px;
}}

.masthead-left {{
    display: flex;
    flex-direction: column;
    gap: 0;
}}

.masthead-eyebrow {{
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {T['ink_4']};
    margin-bottom: 20px;
    font-family: {T['sans']};
}}

.masthead-title {{
    font-size: clamp(52px, 6vw, 96px);
    font-weight: 700;
    line-height: 0.92;
    letter-spacing: -0.035em;
    color: {T['ink']};
    font-family: {T['sans']};
}}

.masthead-title span {{
    color: {T['ink_3']};
    font-weight: 300;
}}

.masthead-right {{
    text-align: right;
    padding-bottom: 6px;
}}

.masthead-period {{
    font-size: 13px;
    font-weight: 400;
    color: {T['ink_4']};
    font-family: {T['mono']};
    letter-spacing: 0.04em;
    line-height: 1.8;
}}

.masthead-tag {{
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {T['cobalt']};
    border: 1px solid {T['cobalt']};
    padding: 3px 8px;
    margin-top: 10px;
}}

/* ── Navigation ───────────────────────────────────────────── */
.nav-strip {{
    border-bottom: 1px solid {T['rule']};
    margin-bottom: 0;
    background: {T['bg']};
    position: sticky;
    top: 0;
    z-index: 100;
}}

.stTabs {{
    background: transparent !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    background: transparent !important;
    border: none !important;
    gap: 0 !important;
    padding: 0 !important;
    border-radius: 0 !important;
    max-width: 1440px;
    margin: 0 auto;
    padding: 0 64px !important;
}}

.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 18px 0 !important;
    margin-right: 48px !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: {T['ink_4']} !important;
    font-family: {T['sans']} !important;
    transition: color 0.2s ease !important;
    position: relative;
}}

.stTabs [data-baseweb="tab"]:hover {{
    color: {T['ink']} !important;
}}

.stTabs [aria-selected="true"] {{
    color: {T['ink']} !important;
    border-bottom: 2px solid {T['ink']} !important;
}}

.stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
.stTabs [data-baseweb="tab-border"] {{ display: none !important; }}
.stTabs [data-baseweb="tab-panel"] {{
    padding: 0 !important;
    background: transparent !important;
}}

/* ── Stat bar ─────────────────────────────────────────────── */
.stat-bar {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border-bottom: 1px solid {T['rule']};
}}

.stat-cell {{
    padding: 44px 0 40px 0;
    border-right: 1px solid {T['rule_light']};
    padding-right: 40px;
    margin-right: 0;
}}

.stat-cell:first-child {{ padding-left: 0; }}
.stat-cell:last-child {{ border-right: none; padding-left: 40px; }}
.stat-cell:nth-child(2) {{ padding-left: 40px; }}
.stat-cell:nth-child(3) {{ padding-left: 40px; }}

.stat-number {{
    font-size: clamp(36px, 4vw, 60px);
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.03em;
    color: {T['ink']};
    font-family: {T['mono']};
    margin-bottom: 10px;
}}

.stat-number.accent {{ color: {T['red']}; }}
.stat-number.cobalt {{ color: {T['cobalt']}; }}

.stat-label {{
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: {T['ink_4']};
    margin-bottom: 4px;
}}

.stat-sub {{
    font-size: 12px;
    color: {T['ink_3']};
    line-height: 1.5;
    margin-top: 4px;
    font-family: {T['sans']};
}}

/* ── Section headers ──────────────────────────────────────── */
.section-header {{
    display: grid;
    grid-template-columns: 80px 1fr;
    gap: 0;
    align-items: start;
    padding: 64px 0 40px 0;
    border-bottom: 1px solid {T['rule_light']};
    margin-bottom: 0;
}}

.section-num {{
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {T['ink_4']};
    padding-top: 8px;
    font-family: {T['mono']};
}}

.section-title-block {{
    display: flex;
    flex-direction: column;
    gap: 12px;
}}

.section-h {{
    font-size: clamp(28px, 3.5vw, 48px);
    font-weight: 700;
    line-height: 1.0;
    letter-spacing: -0.025em;
    color: {T['ink']};
}}

.section-desc {{
    font-size: 14px;
    color: {T['ink_3']};
    line-height: 1.6;
    max-width: 520px;
    font-weight: 400;
}}

/* ── Content grid ─────────────────────────────────────────── */
.content-row {{
    display: grid;
    gap: 1px;
    background: {T['rule_light']};
    margin-bottom: 1px;
}}

.content-row-2 {{ grid-template-columns: 3fr 2fr; }}
.content-row-3 {{ grid-template-columns: 1fr 1fr 1fr; }}
.content-row-full {{ grid-template-columns: 1fr; }}

.content-cell {{
    background: {T['bg']};
    padding: 48px;
}}

/* ── Chart labels ─────────────────────────────────────────── */
.chart-label {{
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {T['ink_4']};
    margin-bottom: 20px;
    font-family: {T['sans']};
}}

/* ── Inline stat ──────────────────────────────────────────── */
.inline-stat {{
    border-top: 1px solid {T['rule_light']};
    padding: 24px 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
}}

.inline-stat + .inline-stat {{
    border-top: 1px solid {T['rule_light']};
}}

.inline-stat-val {{
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.02em;
    font-family: {T['mono']};
    color: {T['ink']};
    line-height: 1;
}}

.inline-stat-label {{
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {T['ink_4']};
    margin-top: 6px;
}}

/* ── Status pill ──────────────────────────────────────────── */
.status-block {{
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 24px 0;
    border-top: 1px solid {T['rule_light']};
}}

.status-indicator {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    margin-top: 6px;
    flex-shrink: 0;
}}

.status-ok    {{ background: {T['green_ink']}; }}
.status-warn  {{ background: {T['red']}; }}
.status-info  {{ background: {T['cobalt']}; }}

.status-text  {{ font-size: 13px; color: {T['ink_2']}; line-height: 1.6; }}
.status-label {{ font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: {T['ink_4']}; margin-bottom: 4px; }}

/* ── Compliance check ─────────────────────────────────────── */
.compliance-item {{
    display: grid;
    grid-template-columns: 60px 1fr;
    gap: 0;
    align-items: center;
    padding: 18px 0;
    border-bottom: 1px solid {T['rule_light']};
}}

.compliance-item:last-child {{ border-bottom: none; }}

.compliance-mark-pass {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: {T['green_ink']};
    font-family: {T['mono']};
}}

.compliance-mark-fail {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: {T['red']};
    font-family: {T['mono']};
}}

.compliance-text {{
    font-size: 13px;
    color: {T['ink_2']};
    line-height: 1.4;
}}

.compliance-sub {{
    font-size: 11px;
    color: {T['ink_4']};
    margin-top: 2px;
}}

/* ── Data rows ────────────────────────────────────────────── */
.data-row {{
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: baseline;
    gap: 24px;
    padding: 14px 0;
    border-bottom: 1px solid {T['rule_light']};
}}

.data-row:last-child {{ border-bottom: none; }}

.data-row-label {{
    font-size: 13px;
    color: {T['ink_2']};
}}

.data-row-value {{
    font-size: 15px;
    font-weight: 600;
    font-family: {T['mono']};
    color: {T['ink']};
    letter-spacing: -0.01em;
    text-align: right;
    white-space: nowrap;
}}

.data-row-value.red {{ color: {T['red']}; }}
.data-row-value.cobalt {{ color: {T['cobalt']}; }}
.data-row-value.muted {{ color: {T['ink_3']}; }}

/* ── Flag severity ────────────────────────────────────────── */
.sev-tag {{
    display: inline-block;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 2px 6px;
    font-family: {T['mono']};
}}

.sev-critical {{ color: {T['red']};    border: 1px solid {T['red']};    background: #A81C1C08; }}
.sev-high     {{ color: {T['amber']};  border: 1px solid {T['amber']};  background: #7A5C0008; }}
.sev-moderate {{ color: {T['cobalt']}; border: 1px solid {T['cobalt']}; background: #1B3D6B08; }}
.sev-ok       {{ color: {T['ink_4']};  border: 1px solid {T['rule']};   background: transparent; }}

/* ── Methodology block ────────────────────────────────────── */
.method-block {{
    background: {T['surface']};
    padding: 40px 48px;
    border-left: 2px solid {T['ink']};
    margin: 48px 0;
}}

.method-title {{
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {T['ink_3']};
    margin-bottom: 16px;
}}

.method-body {{
    font-size: 13px;
    line-height: 1.75;
    color: {T['ink_2']};
    max-width: 680px;
}}

.method-body strong {{ color: {T['ink']}; font-weight: 600; }}

/* ── QoQ note ─────────────────────────────────────────────── */
.qoq-note {{
    padding: 32px 0;
    border-top: 1px solid {T['rule']};
    border-bottom: 1px solid {T['rule']};
    display: grid;
    grid-template-columns: 80px 1fr;
    gap: 24px;
    align-items: start;
    margin-top: 48px;
}}

.qoq-label {{
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {T['ink_4']};
    padding-top: 3px;
    font-family: {T['mono']};
}}

.qoq-text {{
    font-size: 13px;
    color: {T['ink_3']};
    line-height: 1.6;
}}

/* ── Footer ───────────────────────────────────────────────── */
.ci-footer {{
    border-top: 1px solid {T['rule']};
    padding: 32px 0 64px 0;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-top: 80px;
}}

.footer-note {{
    font-size: 11px;
    color: {T['ink_4']};
    line-height: 1.6;
}}

/* ── Expandable ───────────────────────────────────────────── */
.streamlit-expanderHeader {{
    background: transparent !important;
    border: none !important;
    border-top: 1px solid {T['rule_light']} !important;
    border-radius: 0 !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: {T['ink_4']} !important;
    padding: 16px 0 !important;
}}

.streamlit-expanderContent {{
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
}}

/* ── Dataframe ────────────────────────────────────────────── */
.stDataFrame {{ border: none !important; }}

div[data-testid="stDataFrame"] > div {{
    border: 1px solid {T['rule']} !important;
    border-radius: 0 !important;
}}

/* ── Plot container ───────────────────────────────────────── */
div[data-testid="stPlotlyChart"] > div {{
    border: none !important;
}}
</style>
""", unsafe_allow_html=True)


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load(query: str) -> pd.DataFrame:
    con = duckdb.connect(DB_PATH, read_only=True)
    df  = con.execute(query).df()
    con.close()
    return df


# ── Chart theme ────────────────────────────────────────────────────────────────
def chart_theme(height: int = 340) -> dict:
    return dict(
        plot_bgcolor  = T["bg"],
        paper_bgcolor = T["bg"],
        height        = height,
        margin        = dict(l=0, r=0, t=8, b=0),
        font          = dict(family="Helvetica Neue, Helvetica, Arial, sans-serif",
                             color=T["ink_3"], size=11),
        xaxis=dict(
            gridcolor    = T["rule_light"],
            linecolor    = T["rule"],
            tickcolor    = T["rule"],
            tickfont     = dict(size=10, color=T["ink_4"]),
            showline     = True,
            linewidth    = 1,
        ),
        yaxis=dict(
            gridcolor    = T["rule_light"],
            linecolor    = T["rule"],
            tickcolor    = T["rule"],
            tickfont     = dict(size=10, color=T["ink_4"]),
            showline     = False,
            showgrid     = True,
        ),
        legend=dict(
            bgcolor      = "rgba(0,0,0,0)",
            borderwidth  = 0,
            font         = dict(size=10, color=T["ink_3"]),
            orientation  = "h",
            x            = 0,
            y            = 1.08,
        ),
        hoverlabel=dict(
            bgcolor     = T["ink"],
            bordercolor = T["ink"],
            font        = dict(color="white", size=11),
        ),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=T["ink_4"], activecolor=T["ink"]),
    )


def sev_color_map(s: str) -> str:
    return {"critical": T["red"], "high": T["amber"], "moderate": T["cobalt"],
            "within_norms": T["ink_4"]}.get(s, T["ink_4"])


def sev_class(s: str) -> str:
    return {"critical": "sev-critical", "high": "sev-high",
            "moderate": "sev-moderate", "within_norms": "sev-ok"}.get(s, "sev-ok")


def short(cat: str, n: int = 28) -> str:
    return (cat.replace("KEYWORD_", "").replace("STATEMENT_CATEGORY_", "")
               .replace("_", " ").title()[:n])


def data_row(label: str, value: str, cls: str = "") -> None:
    st.markdown(f"""
<div class="data-row">
  <span class="data-row-label">{label}</span>
  <span class="data-row-value {cls}">{value}</span>
</div>""", unsafe_allow_html=True)


# ── Load all data upfront ──────────────────────────────────────────────────────
summary = load("SELECT * FROM main_marts.mart_enforcement_summary")
appeals = load("SELECT * FROM main_intermediate.int_appeal_outcomes")
equity  = load("SELECT * FROM main_marts.mart_equity_audit")
reg     = load("SELECT * FROM main_marts.mart_regulatory_summary")

total_measures   = int(summary["total_measures"].sum())
total_removals   = int(summary["total_removals"].sum())
total_automated  = int(summary["automated_measures"].sum())
auto_pct         = total_automated / max(total_measures, 1) * 100
n_flagged        = int(equity["disparate_impact_flag"].sum())

ap = appeals.iloc[0].to_dict() if not appeals.empty else {}
rr = reg.iloc[0].to_dict() if not reg.empty else {}


# ══════════════════════════════════════════════════════════════════════════════
# MASTHEAD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="ci-wrapper">
  <div class="masthead">
    <div class="masthead-grid">
      <div class="masthead-left">
        <div class="masthead-eyebrow">Digital Services Act &mdash; Compliance Analytics</div>
        <div class="masthead-title">DSA COMPLIANCE<br><span>INTELLIGENCE</span></div>
      </div>
      <div class="masthead-right">
        <div class="masthead-period">
          Period&nbsp;&nbsp;&nbsp;2025-01-01 / 2025-12-31<br>
          Report&nbsp;&nbsp;&nbsp;Annual Transparency Filing<br>
          Source&nbsp;&nbsp;&nbsp;Official DSA Transparency Report
        </div>
        <div class="masthead-tag">53 Tests Passing</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION (Streamlit tabs wrapped in Swiss nav strip)
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "01&nbsp;&nbsp;Enforcement",
    "02&nbsp;&nbsp;Appeals",
    "03&nbsp;&nbsp;Equity Audit",
    "04&nbsp;&nbsp;Regulatory",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 01 - ENFORCEMENT
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown(f"""
<div class="ci-wrapper">

  <div class="stat-bar">
    <div class="stat-cell">
      <div class="stat-label">Total Actions</div>
      <div class="stat-number">{total_measures:,}</div>
      <div class="stat-sub">Proactive enforcement measures</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">Content Removals</div>
      <div class="stat-number cobalt">{total_removals:,}</div>
      <div class="stat-sub">Visibility restriction type</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">Automated Rate</div>
      <div class="stat-number">{auto_pct:.1f}%</div>
      <div class="stat-sub">Solely automated decisions</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">Flagged Categories</div>
      <div class="stat-number accent">{n_flagged}</div>
      <div class="stat-sub">Disparate impact threshold exceeded</div>
    </div>
  </div>

  <div class="section-header">
    <div class="section-num">01</div>
    <div class="section-title-block">
      <div class="section-h">Enforcement Breakdown</div>
      <div class="section-desc">
        Proactive content moderation actions across illegal content and Terms &amp; Conditions
        categories. Stacked view shows automated vs human-review split per category.
      </div>
    </div>
  </div>

</div>
""", unsafe_allow_html=True)

    # ── Main chart: stacked horizontal bar ────────────────────────────────────
    st.markdown('<div class="ci-wrapper">', unsafe_allow_html=True)

    col_chart, col_aside = st.columns([5, 2], gap="large")

    with col_chart:
        st.markdown('<div class="chart-label">Enforcement Volume by Category (Top 20)</div>', unsafe_allow_html=True)
        top20 = (
            summary.groupby("category")[["total_measures", "automated_measures"]]
            .sum().nlargest(20, "total_measures").reset_index()
        )
        top20["manual"]    = top20["total_measures"] - top20["automated_measures"]
        top20["cat_label"] = top20["category"].apply(lambda c: short(c, 32))

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=top20["cat_label"], x=top20["automated_measures"],
            name="Automated", orientation="h",
            marker=dict(color=T["ink"], opacity=0.85),
            hovertemplate="%{x:,}<extra>Automated</extra>",
        ))
        fig.add_trace(go.Bar(
            y=top20["cat_label"], x=top20["manual"],
            name="Human Review", orientation="h",
            marker=dict(color=T["ink_4"], opacity=0.55),
            hovertemplate="%{x:,}<extra>Human Review</extra>",
        ))
        tk = chart_theme(560)
        tk["yaxis"]["autorange"] = "reversed"
        tk["yaxis"]["tickfont"]  = dict(size=11, color=T["ink_3"])
        tk["xaxis"]["title"]     = dict(text="Enforcement Measures", font=dict(size=10, color=T["ink_4"]))
        fig.update_layout(**tk, barmode="stack", bargap=0.35)
        st.plotly_chart(fig, width="stretch")

    with col_aside:
        by_type = summary.groupby("enforcement_type")["total_measures"].sum()
        ill_total = int(by_type.get("illegal_content", 0))
        tc_total  = int(by_type.get("terms_and_conditions", 0))

        st.markdown(f"""
<div style="padding-top:32px">
  <div class="chart-label">By Enforcement Type</div>
  <div class="inline-stat">
    <div class="inline-stat-val">{ill_total:,}</div>
    <div class="inline-stat-label">Illegal Content</div>
  </div>
  <div class="inline-stat">
    <div class="inline-stat-val">{tc_total:,}</div>
    <div class="inline-stat-label">Terms &amp; Conditions</div>
  </div>
</div>
""", unsafe_allow_html=True)

        tier = summary.groupby("enforcement_tier")["total_measures"].sum()
        t5   = int(tier.get("top_5", 0))
        t10  = int(tier.get("top_10", 0))
        tail = int(tier.get("long_tail", 0))

        st.markdown(f"""
<div style="padding-top:40px">
  <div class="chart-label">Enforcement Tier</div>
  <div class="inline-stat">
    <div class="inline-stat-val">{t5:,}</div>
    <div class="inline-stat-label">Top 5 categories</div>
  </div>
  <div class="inline-stat">
    <div class="inline-stat-val">{t10:,}</div>
    <div class="inline-stat-label">Top 6-10 categories</div>
  </div>
  <div class="inline-stat">
    <div class="inline-stat-val">{tail:,}</div>
    <div class="inline-stat-label">Long-tail categories</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Treemap ───────────────────────────────────────────────────────────────
    st.markdown('<div class="ci-wrapper">', unsafe_allow_html=True)
    st.markdown(f"""
<div style="border-top:1px solid {T['rule_light']};padding-top:48px;margin-top:0;">
  <div class="chart-label">Enforcement Landscape</div>
</div>
""", unsafe_allow_html=True)

    tm = summary[summary["total_measures"] > 0].copy()
    tm["cat_label"]  = tm["category"].apply(lambda c: short(c, 26))
    tm["type_label"] = tm["enforcement_type"].str.replace("_", " ").str.title()

    fig_tm = px.treemap(
        tm, path=["type_label", "cat_label"], values="total_measures",
        color="total_measures",
        color_continuous_scale=[[0, "#DDDAD5"], [0.4, T["ink_3"]], [1, T["ink"]]],
    )
    tk_tm                = chart_theme(320)
    tk_tm["margin"]      = dict(l=0, r=0, t=0, b=0)
    tk_tm["coloraxis_showscale"] = False
    fig_tm.update_layout(**tk_tm)
    fig_tm.update_traces(
        textfont=dict(size=11, color="white"),
        marker=dict(line=dict(width=1.5, color=T["bg"])),
        hovertemplate="<b>%{label}</b><br>%{value:,} actions<extra></extra>",
    )
    st.plotly_chart(fig_tm, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 02 - APPEALS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    if not ap:
        st.warning("No appeal data loaded.")
    else:
        total_complaints = int(ap.get("total_complaints_submitted") or 0)
        total_mod        = int(ap.get("total_moderation_actions") or 0)
        total_auto_ap    = int(ap.get("total_automated_actions") or 0)
        total_human_ap   = int(ap.get("total_human_review_actions") or 0)
        appeal_rate      = float(ap.get("appeal_rate") or 0)
        auto_rate        = float(ap.get("automation_rate") or 0)
        accuracy         = float(ap.get("automation_accuracy") or 0)
        precision_v      = float(ap.get("automation_precision") or 0)
        recall_v         = float(ap.get("automation_recall") or 0)
        fp_proxy         = float(ap.get("false_positive_rate_proxy") or 0)
        fn_proxy         = float(ap.get("false_negative_rate_proxy") or 0)
        per_10k          = float(ap.get("complaints_per_10k_actions") or 0)
        risk_flag        = bool(ap.get("compliance_risk_flag") or False)
        risk_desc        = str(ap.get("compliance_risk_description") or "")

        risk_class = "status-warn" if risk_flag else "status-ok"
        risk_label = "Compliance concern flagged" if risk_flag else "Within compliance thresholds"

        st.markdown(f"""
<div class="ci-wrapper">

  <div class="stat-bar">
    <div class="stat-cell">
      <div class="stat-label">Complaints Filed</div>
      <div class="stat-number">{total_complaints:,}</div>
      <div class="stat-sub">DSA Article 20 internal mechanism</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">Total Moderation Actions</div>
      <div class="stat-number cobalt">{total_mod:,}</div>
      <div class="stat-sub">{total_auto_ap:,} automated &middot; {total_human_ap:,} human</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">Appeal Rate</div>
      <div class="stat-number">{appeal_rate*100:.2f}%</div>
      <div class="stat-sub">Complaints per moderation action</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">Automation Rate</div>
      <div class="stat-number">{auto_rate*100:.1f}%</div>
      <div class="stat-sub">Solely automated decisions</div>
    </div>
  </div>

  <div class="section-header">
    <div class="section-num">02</div>
    <div class="section-title-block">
      <div class="section-h">Appeal Outcomes</div>
      <div class="section-desc">
        Internal complaint mechanism data (DSA Article 20) combined with automated
        system performance metrics. Precision and recall proxy for enforcement accuracy.
      </div>
    </div>
  </div>

  <div style="padding-bottom: 0">
    <div class="status-block">
      <div class="status-indicator {risk_class}"></div>
      <div>
        <div class="status-label">{risk_label}</div>
        <div class="status-text">{risk_desc}</div>
      </div>
    </div>
  </div>

</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="ci-wrapper">', unsafe_allow_html=True)
        col_left, col_right = st.columns([3, 2], gap="large")

        with col_left:
            st.markdown('<div class="chart-label">Automated System Performance (%)</div>', unsafe_allow_html=True)

            fig_perf = go.Figure()
            metrics  = [("Accuracy", accuracy), ("Precision", precision_v), ("Recall", recall_v)]
            bar_clrs = [T["ink"], T["ink_3"], T["ink_4"]]
            for (name, val), clr in zip(metrics, bar_clrs):
                fig_perf.add_trace(go.Bar(
                    x=[name], y=[val * 100], name=name,
                    marker=dict(color=clr),
                    text=[f"{val*100:.4f}%"],
                    textposition="outside",
                    textfont=dict(size=11, color=T["ink_2"]),
                    hovertemplate=f"<b>{name}</b>: %{{y:.6f}}%<extra></extra>",
                ))
            tk_p = chart_theme(300)
            tk_p["yaxis"]["range"]     = [93, 100.4]
            tk_p["yaxis"]["ticksuffix"] = "%"
            tk_p["bargap"]             = 0.5
            fig_perf.update_layout(**tk_p, showlegend=False)
            st.plotly_chart(fig_perf, width="stretch")

            st.markdown('<div class="chart-label" style="margin-top:32px">System Performance Radar</div>', unsafe_allow_html=True)
            fig_r = go.Figure(go.Scatterpolar(
                r=[accuracy * 100, precision_v * 100, recall_v * 100, accuracy * 100],
                theta=["Accuracy", "Precision", "Recall", "Accuracy"],
                fill="toself",
                fillcolor="rgba(13,13,13,0.06)",
                line=dict(color=T["ink"], width=1.5),
                mode="lines",
            ))
            fig_r.update_layout(
                **chart_theme(280),
                polar=dict(
                    bgcolor=T["bg"],
                    radialaxis=dict(visible=True, range=[93, 100],
                                   gridcolor=T["rule_light"], linecolor=T["rule"],
                                   tickfont=dict(size=9, color=T["ink_4"])),
                    angularaxis=dict(gridcolor=T["rule_light"],
                                     tickfont=dict(size=10, color=T["ink_3"])),
                ),
            )
            st.plotly_chart(fig_r, width="stretch")

        with col_right:
            st.markdown(f"""
<div style="padding-top:16px">
  <div class="chart-label">Error Rate Proxies</div>
  <div style="margin-top:8px">
""", unsafe_allow_html=True)
            for label, val, note in [
                ("False Positive Rate", f"{fp_proxy*100:.4f}%", "Incorrect flags (1 - Precision)"),
                ("False Negative Rate", f"{fn_proxy*100:.4f}%", "Missed violations (1 - Recall)"),
                ("Complaints / 10k Actions", f"{per_10k:.2f}", "Normalized dispute rate"),
            ]:
                st.markdown(f"""
<div style="border-top:1px solid {T['rule_light']};padding:20px 0">
  <div style="font-size:10px;letter-spacing:0.1em;text-transform:uppercase;
              color:{T['ink_4']};margin-bottom:6px">{label}</div>
  <div style="font-size:26px;font-weight:700;letter-spacing:-0.02em;
              font-family:{T['mono']};color:{T['ink']};line-height:1">{val}</div>
  <div style="font-size:11px;color:{T['ink_4']};margin-top:6px">{note}</div>
</div>
""", unsafe_allow_html=True)

            st.markdown(f"""
  </div>
  <div class="chart-label" style="margin-top:32px">Action Breakdown</div>
""", unsafe_allow_html=True)

            fig_d = go.Figure(go.Pie(
                labels=["Automated", "Human Review"],
                values=[total_auto_ap, total_human_ap],
                hole=0.68,
                marker=dict(colors=[T["ink"], T["ink_4"]], line=dict(color=T["bg"], width=3)),
                textfont=dict(size=10),
                textinfo="label+percent",
            ))
            fig_d.add_annotation(
                text=f"<b>{total_mod:,}</b>", showarrow=False,
                font=dict(size=16, color=T["ink"], family="JetBrains Mono, monospace"),
            )
            fig_d.update_layout(**chart_theme(240), showlegend=False)
            st.plotly_chart(fig_d, width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"""
<div class="method-block">
  <div class="method-title">Data Disclosure Note</div>
  <div class="method-body">
    The DSA transparency report discloses only aggregate complaint counts for the reporting period.
    Category-level appeal rates and overturn rates are not included in the public filing.
    A production pipeline would join to internal case management data to surface per-category
    reversal rates, the strongest signal of systematic over-enforcement. The <strong>automation_rate</strong>
    and <strong>false_positive_rate_proxy</strong> columns in this model serve as compliant proxies
    until that data is available.
  </div>
</div>
""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 03 - EQUITY AUDIT
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    flagged_df = equity[equity["disparate_impact_flag"] == True]
    n_total    = len(equity)
    n_flagged  = len(flagged_df)
    n_crit     = len(equity[equity["disparate_impact_severity"] == "critical"])
    n_high     = len(equity[equity["disparate_impact_severity"] == "high"])

    st.markdown(f"""
<div class="ci-wrapper">

  <div class="stat-bar">
    <div class="stat-cell">
      <div class="stat-label">Categories Analyzed</div>
      <div class="stat-number">{n_total}</div>
      <div class="stat-sub">Across all enforcement types</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">Flagged for Review</div>
      <div class="stat-number accent">{n_flagged}</div>
      <div class="stat-sub">{n_flagged/max(n_total,1)*100:.0f}% of total categories</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">Critical Severity</div>
      <div class="stat-number accent">{n_crit}</div>
      <div class="stat-sub">Greater than 3x platform average</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">High Severity</div>
      <div class="stat-number">{n_high}</div>
      <div class="stat-sub">Greater than 2x platform average</div>
    </div>
  </div>

  <div class="section-header">
    <div class="section-num">03</div>
    <div class="section-title-block">
      <div class="section-h">Equity Audit</div>
      <div class="section-desc">
        Disparate impact analysis across content categories. Categories where
        enforcement rate exceeds 1.5x the platform average are flagged for
        policy review under the EEOC 4/5ths rule analogue.
      </div>
    </div>
  </div>

</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="ci-wrapper">', unsafe_allow_html=True)

    col_main, col_side = st.columns([3, 2], gap="large")

    with col_main:
        st.markdown('<div class="chart-label">Enforcement Rate vs Platform Average (Top 30 by Rate)</div>', unsafe_allow_html=True)

        plot_df = (equity.nlargest(30, "removal_rate_vs_platform_avg")
                         .sort_values("removal_rate_vs_platform_avg"))
        plot_df["cat_label"] = plot_df["category_code"].apply(lambda c: short(c, 30))
        bar_colors = [sev_color_map(s) for s in plot_df["disparate_impact_severity"]]

        fig_eq = go.Figure()
        fig_eq.add_trace(go.Bar(
            x=plot_df["removal_rate_vs_platform_avg"],
            y=plot_df["cat_label"],
            orientation="h",
            marker=dict(color=bar_colors, opacity=0.9),
            hovertemplate="<b>%{y}</b><br>Rate: %{x:.2f}x<extra></extra>",
        ))
        fig_eq.add_vline(
            x=1.5, line_dash="dash", line_color=T["red"], line_width=1,
            annotation_text="1.5x threshold",
            annotation_font=dict(color=T["red"], size=9),
            annotation_position="top",
        )
        fig_eq.add_vline(
            x=1.0, line_dash="dot", line_color=T["rule"], line_width=1,
            annotation_text="platform avg",
            annotation_font=dict(color=T["ink_4"], size=9),
        )
        tk_eq = chart_theme(580)
        tk_eq["yaxis"]["tickfont"] = dict(size=10, color=T["ink_3"])
        tk_eq["xaxis"]["title"]    = dict(text="Rate vs Platform Average",
                                          font=dict(size=10, color=T["ink_4"]))
        fig_eq.update_layout(**tk_eq, bargap=0.30)
        st.plotly_chart(fig_eq, width="stretch")

    with col_side:
        st.markdown('<div class="chart-label">Severity Distribution</div>', unsafe_allow_html=True)
        sev_order  = ["critical", "high", "moderate", "within_norms"]
        sev_labels = ["Critical", "High", "Moderate", "Within Norms"]
        sev_counts = (equity.groupby("disparate_impact_severity").size()
                            .reindex(sev_order, fill_value=0))

        fig_sev = go.Figure(go.Bar(
            x=sev_labels,
            y=sev_counts.values,
            marker=dict(
                color=[sev_color_map(s) for s in sev_order],
                opacity=0.85,
            ),
            text=sev_counts.values,
            textposition="outside",
            textfont=dict(size=11, color=T["ink_3"]),
            hovertemplate="<b>%{x}</b><br>%{y} categories<extra></extra>",
        ))
        fig_sev.update_layout(**chart_theme(220), showlegend=False, bargap=0.45)
        st.plotly_chart(fig_sev, width="stretch")

        st.markdown(f"""
<div style="margin-top:16px">
  <div class="chart-label">Z-Score Distribution</div>
</div>
""", unsafe_allow_html=True)

        z_data = equity.dropna(subset=["enforcement_z_score"])
        if not z_data.empty:
            fig_z = go.Figure(go.Histogram(
                x=z_data["enforcement_z_score"], nbinsx=18,
                marker=dict(color=T["ink"], opacity=0.7,
                            line=dict(color=T["bg"], width=1)),
                hovertemplate="Z: %{x:.2f}<br>Count: %{y}<extra></extra>",
            ))
            fig_z.add_vline(x=0, line_color=T["rule"], line_dash="dot", line_width=1)
            tk_z = chart_theme(180)
            tk_z["xaxis"]["title"] = dict(text="Z-Score", font=dict(size=10, color=T["ink_4"]))
            tk_z["yaxis"]["title"] = dict(text="Count",   font=dict(size=10, color=T["ink_4"]))
            fig_z.update_layout(**tk_z, showlegend=False)
            st.plotly_chart(fig_z, width="stretch")

        st.markdown('<div class="chart-label" style="margin-top:24px">By Enforcement Type</div>', unsafe_allow_html=True)
        by_type_eq = equity.groupby("enforcement_type").agg(
            flagged=("disparate_impact_flag", "sum"),
            total=("disparate_impact_flag", "count"),
        ).reset_index()
        for _, rw in by_type_eq.iterrows():
            pct  = rw["flagged"] / max(rw["total"], 1) * 100
            clr  = "red" if pct > 30 else ("muted" if pct < 10 else "cobalt")
            st.markdown(f"""
<div class="data-row">
  <span class="data-row-label">{rw['enforcement_type'].replace('_',' ').title()}</span>
  <span class="data-row-value {clr}">{int(rw['flagged'])}/{int(rw['total'])}</span>
</div>
""", unsafe_allow_html=True)

    # ── Scatter ───────────────────────────────────────────────────────────────
    st.markdown(f"""
<div style="border-top:1px solid {T['rule_light']};padding-top:48px;margin-top:16px">
  <div class="chart-label">Volume vs Statistical Outlier Score</div>
</div>
""", unsafe_allow_html=True)

    sc = equity.dropna(subset=["enforcement_z_score"]).copy()
    sc["cat_label"] = sc["category_code"].apply(lambda c: short(c, 20))

    fig_sc = go.Figure()
    for sev in sev_order:
        sub = sc[sc["disparate_impact_severity"] == sev]
        if sub.empty:
            continue
        fig_sc.add_trace(go.Scatter(
            x=sub["category_removals"], y=sub["enforcement_z_score"],
            mode="markers+text",
            name=sev.replace("_", " ").title(),
            text=sub["cat_label"],
            textposition="top center",
            textfont=dict(size=9, color=T["ink_4"]),
            marker=dict(color=sev_color_map(sev), size=9, opacity=0.85,
                        line=dict(color=T["bg"], width=1.5)),
            hovertemplate="<b>%{text}</b><br>Removals: %{x:,}<br>Z-Score: %{y:.2f}<extra></extra>",
        ))
    fig_sc.add_hline(y=0, line_color=T["rule_light"], line_dash="dot", line_width=1)
    tk_sc = chart_theme(300)
    tk_sc["xaxis"]["title"] = dict(text="Category Removals", font=dict(size=10, color=T["ink_4"]))
    tk_sc["yaxis"]["title"] = dict(text="Enforcement Z-Score", font=dict(size=10, color=T["ink_4"]))
    fig_sc.update_layout(**tk_sc)
    st.plotly_chart(fig_sc, width="stretch")

    # ── Methodology block ─────────────────────────────────────────────────────
    st.markdown(f"""
<div class="method-block">
  <div class="method-title">Methodology</div>
  <div class="method-body">
    <strong>Disparate impact threshold: 1.5x platform average.</strong> For each content category,
    the enforcement rate is the category's removal count divided by the per-category platform average
    (total removals / number of active categories within each enforcement type). Categories exceeding
    <strong>1.5x</strong> this baseline are flagged for review. Severity tiers: critical (&gt;3x),
    high (&gt;2x), moderate (&gt;1.5x). Z-scores measure deviation from the cross-category mean in
    units of standard deviation.<br><br>
    The 1.5x threshold follows heuristics analogous to the <strong>EEOC 4/5ths rule</strong> applied to
    content enforcement. Overturn rates are not disclosed at category level in the public filing;
    a production system would join to internal case management data to complete this picture.
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Audit table ───────────────────────────────────────────────────────────
    if not flagged_df.empty:
        st.markdown(f"""
<div style="border-top:1px solid {T['rule']};padding-top:48px;margin-top:0">
  <div class="chart-label">Flagged Categories - Audit Detail</div>
</div>
""", unsafe_allow_html=True)
        disp  = ["enforcement_type", "category_code", "category_description",
                 "category_removals", "removal_rate_vs_platform_avg",
                 "enforcement_z_score", "disparate_impact_severity", "audit_action"]
        avail = [c for c in disp if c in flagged_df.columns]
        show  = flagged_df[avail].sort_values("removal_rate_vs_platform_avg", ascending=False).copy()
        show.columns = [c.replace("_", " ").title() for c in show.columns]
        st.dataframe(show, width="stretch", hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 04 - REGULATORY SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    if rr is None:
        st.warning("No regulatory data loaded.")
    else:
        total_enf  = int(rr.get("total_enforcement_actions") or 0)
        total_comp = int(rr.get("user_complaints_received") or 0)
        comp_cats  = int(rr.get("content_categories_with_enforcement") or 0)
        tc_flagged = int(rr.get("categories_flagged_disparate_impact") or 0)
        tc_total   = int(rr.get("total_categories_analyzed") or 0)

        st.markdown(f"""
<div class="ci-wrapper">

  <div class="stat-bar">
    <div class="stat-cell">
      <div class="stat-label">Enforcement Actions</div>
      <div class="stat-number">{total_enf:,}</div>
      <div class="stat-sub">Total across all categories</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">User Complaints</div>
      <div class="stat-number cobalt">{total_comp:,}</div>
      <div class="stat-sub">DSA Article 20 mechanism</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">Categories Active</div>
      <div class="stat-number">{comp_cats}</div>
      <div class="stat-sub">With enforcement activity</div>
    </div>
    <div class="stat-cell">
      <div class="stat-label">Equity Flags</div>
      <div class="stat-number accent">{tc_flagged}</div>
      <div class="stat-sub">of {tc_total} categories analyzed</div>
    </div>
  </div>

  <div class="section-header">
    <div class="section-num">04</div>
    <div class="section-title-block">
      <div class="section-h">Regulatory Summary</div>
      <div class="section-desc">
        Annual compliance snapshot designed for legal counsel and policy leads.
        DSA article coverage, enforcement KPIs, and automation performance
        in a single auditable view.
      </div>
    </div>
  </div>

</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="ci-wrapper">', unsafe_allow_html=True)

        # ── DSA checklist ─────────────────────────────────────────────────────
        st.markdown('<div class="chart-label">DSA Article Compliance Checklist</div>', unsafe_allow_html=True)
        checks = [
            ("Art. 16", "Notices from users and Trusted Flaggers reported",
             bool(rr.get("dsa_article_16_notices_reported"))),
            ("Art. 17", "Own-initiative enforcement activity disclosed",
             bool(rr.get("dsa_article_17_own_initiative_reported"))),
            ("Art. 20", "Internal complaint mechanism data included",
             bool(rr.get("dsa_article_20_complaint_mechanism_reported"))),
            ("Art. 23", "Annual transparency report published",
             bool(rr.get("dsa_article_23_transparency_report_published"))),
        ]
        for art, desc, passed in checks:
            mark  = "PASS" if passed else "FAIL"
            cls   = "compliance-mark-pass" if passed else "compliance-mark-fail"
            st.markdown(f"""
<div class="compliance-item">
  <div class="{cls}">{mark}</div>
  <div>
    <div class="compliance-text"><strong>{art}</strong> &ensp; {desc}</div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown(f"<div style='height:48px'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown('<div class="chart-label">Enforcement Metrics</div>', unsafe_allow_html=True)
            data_rows_enf = [
                ("Total enforcement actions",    f"{int(rr.get('total_enforcement_actions') or 0):,}",    ""),
                ("Actions by automated systems", f"{int(rr.get('actions_by_automated_systems') or 0):,}",  "cobalt"),
                ("Accounts permanently removed", f"{int(rr.get('accounts_permanently_removed') or 0):,}",  "red"),
                ("High-risk category actions",   f"{int(rr.get('high_risk_category_actions') or 0):,}",    "muted"),
            ]
            for label, val, cls in data_rows_enf:
                data_row(label, val, cls)

            st.markdown(f"<div style='height:40px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="chart-label">Appeals and Compliance</div>', unsafe_allow_html=True)

            cf  = bool(rr.get("compliance_concern_flagged") or False)
            cd  = str(rr.get("compliance_concern_detail") or "")
            ind = "status-warn" if cf else "status-ok"
            st.markdown(f"""
<div class="status-block" style="margin-bottom:8px">
  <div class="status-indicator {ind}"></div>
  <div>
    <div class="status-label">{"Concern flagged" if cf else "Within thresholds"}</div>
    <div class="status-text">{cd}</div>
  </div>
</div>
""", unsafe_allow_html=True)
            data_row("User complaints received",
                     f"{int(rr.get('user_complaints_received') or 0):,}", "cobalt")
            data_row("Appeal rate",
                     f"{rr.get("appeal_rate_pct") or 0:.2f}%", "muted")
            data_row("Automation rate",
                     f"{rr.get('automation_rate_pct') or 0:.1f}%", "muted")

        with col2:
            st.markdown('<div class="chart-label">Automation Performance</div>', unsafe_allow_html=True)

            fig_reg = go.Figure()
            for lbl, val in [("Accuracy",  rr.get("automation_accuracy_pct") or 0),
                              ("Precision", rr.get("automation_precision_pct") or 0),
                              ("Recall",    rr.get("automation_recall_pct") or 0)]:
                fig_reg.add_trace(go.Bar(
                    x=[lbl], y=[val],
                    marker=dict(color=T["ink"], opacity=0.85),
                    text=[f"{val:.4f}%"], textposition="outside",
                    textfont=dict(size=11, color=T["ink_3"]),
                    hovertemplate=f"<b>{lbl}</b>: %{{y:.4f}}%<extra></extra>",
                ))
            tk_r = chart_theme(240)
            tk_r["yaxis"]["range"]      = [93, 100.4]
            tk_r["yaxis"]["ticksuffix"] = "%"
            tk_r["bargap"]              = 0.5
            fig_reg.update_layout(**tk_r, showlegend=False)
            st.plotly_chart(fig_reg, width="stretch")

            st.markdown('<div class="chart-label" style="margin-top:32px">Equity Audit Summary</div>', unsafe_allow_html=True)
            pct_f = rr.get("pct_categories_flagged") or 0.0
            data_row("Total categories analyzed", f"{int(rr.get('total_categories_analyzed') or 0)}", "muted")
            data_row("Flagged (disparate impact)", f"{int(rr.get('categories_flagged_disparate_impact') or 0)}", "red")
            data_row("Critical severity",          f"{int(rr.get('critical_severity_count') or 0)}", "red")
            data_row("High severity",              f"{int(rr.get('high_severity_count') or 0)}", "muted")
            data_row("Percent of categories flagged", f"{pct_f:.1f}%", "muted")

        st.markdown(f"""
<div class="qoq-note">
  <div class="qoq-label">QoQ</div>
  <div class="qoq-text">
    {rr.get('qoq_status_note', 'Awaiting prior-period data')}.
    Quarter-over-quarter columns are pre-structured in <code>mart_regulatory_summary</code>
    and will populate automatically when the next reporting cycle is ingested.
  </div>
</div>

<div class="ci-footer">
  <div class="footer-note">
    Data source: Official DSA Transparency Report XLSX (2025 annual filing).<br>
    EU DSA Transparency Database API unavailable during ingestion; gracefully skipped.<br>
    Pipeline: dbt-duckdb &middot; 8 models &middot; 53 tests passing &middot; 3 custom macros
  </div>
  <div class="footer-note" style="text-align:right">
    DSA Compliance Intelligence<br>
    Annual Reporting Period 2025
  </div>
</div>
""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
