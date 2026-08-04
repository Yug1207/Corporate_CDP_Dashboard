# ╔══════════════════════════════════════════════════════════════════════╗
# ║   CDP CLIMATE CHANGE 2024 - FIVE COMPANY DISCLOSURE DASHBOARD        ║
# ║   Adobe · Cognizant · Accenture · Alphabet · Microsoft               ║
# ╚══════════════════════════════════════════════════════════════════════╝


# ═══════════════════════════════════════════════════════════════════════
# CELL 1 - Imports
# ═══════════════════════════════════════════════════════════════════════
import re
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc

# ═══════════════════════════════════════════════════════════════════════
# CELL 2 - Load data
# ═══════════════════════════════════════════════════════════════════════
FILE_PATH = "Companies_CDP_MERGED.xlsx"

raw = pd.read_excel(FILE_PATH, sheet_name="All Matches")
raw["combined_text"] = (
    raw["Question Text"].fillna("") + " " + raw["Answer Text"].fillna("")
).str.strip()
raw["char_length"] = raw["combined_text"].str.len()

COMPANIES = sorted(raw["Company"].unique().tolist())
CATEGORIES = ["Hazard", "Risk", "Mitigation", "Vulnerability"]

# long format: one row per (row, category) so a chunk tagged
# "Risk, Mitigation" counts once toward each
cat_long = raw.assign(category=raw["Matched Category"].str.split(", ")).explode(
    "category"
)

print(f"Loaded {len(raw)} tagged chunks across {len(COMPANIES)} companies")

# ═══════════════════════════════════════════════════════════════════════
# CELL 3 - Extraction logic (keyword scans, duplicate check, $ figures)
# ═══════════════════════════════════════════════════════════════════════
TARGET_KEYWORDS = [
    "science based target", "sbti", "net zero", "net-zero", "carbon neutral",
    "re100", "2030", "2025", "2050", "transition plan",
]
GOV_KEYWORDS = [
    "chief sustainability officer", "board of directors", "audit committee",
    "sustainability committee", "chief trust officer", "chief people officer",
    "general counsel", "chief executive officer",
]
POLICY_KEYWORDS = [
    "regulator", "policy advocacy", "public policy", "trade association",
    "legislation", "policymaker",
]
FINANCE_KEYWORDS = [
    "green bond", "sustainability-linked", "capex", "opex", "credit rating",
    "decarbonizing investment", "climate finance", "financed emissions",
]

FIN_PATTERNS = {
    "Cost of response to risk": r"Cost of response to risk\s*([\d,]{4,})",
    "Financial effect - minimum": r"financial effect figure[^0-9]{0,80}?minimum[^0-9]{0,20}?([\d,]{5,})",
    "Financial effect - maximum": r"financial effect figure[^0-9]{0,80}?maximum[^0-9]{0,20}?([\d,]{5,})",
}


def scan_keywords(frame, keywords):
    """Count keyword hits per company and grab one short excerpt as evidence."""
    pattern = re.compile("|".join(re.escape(k) for k in keywords), re.IGNORECASE)
    rows = []
    for company in COMPANIES:
        g = frame[frame["Company"] == company]
        text = " ".join(g["combined_text"].tolist())
        hits = pattern.findall(text)
        terms = sorted(set(h.lower() for h in hits))
        excerpt = ""
        m = pattern.search(text)
        if m:
            start = max(0, m.start() - 60)
            excerpt = re.sub(r"\s+", " ", text[start : m.end() + 120]).strip()
        rows.append(
            {
                "Company": company,
                "Mentions": len(hits),
                "Terms found": ", ".join(terms[:6]) if terms else "none",
                "Example excerpt": excerpt if excerpt else "no match in the extracted text",
            }
        )
    return pd.DataFrame(rows)


def extract_financial_figures(frame):
    rows = []
    for _, r in frame.iterrows():
        for label, pat in FIN_PATTERNS.items():
            m = re.search(pat, r["combined_text"], re.IGNORECASE)
            if m:
                rows.append(
                    {
                        "Company": r["Company"],
                        "Metric": label,
                        "Amount": int(m.group(1).replace(",", "")),
                    }
                )
    out = pd.DataFrame(rows).drop_duplicates()
    return out


def repeated_code_table(frame):
    rep = frame[frame.duplicated(subset=["Company", "Question Code"], keep=False)].copy()
    if rep.empty:
        return rep
    rep["norm"] = rep["combined_text"].str.lower().str.strip()
    rep["is_dup"] = rep.groupby(["Company", "Question Code"])["norm"].transform(
        lambda s: s.duplicated(keep=False)
    )
    rep["Repeat status"] = rep["is_dup"].map(
        {True: "identical text - copy paste", False: "different content"}
    )
    rep = rep.rename(columns={"Matched Category": "Category", "Answer Type": "Type"})
    return rep[
        ["Company", "Question Code", "Occurrence", "Category", "Type", "Repeat status"]
    ].sort_values(["Company", "Question Code", "Occurrence"])


# ═══════════════════════════════════════════════════════════════════════
# CELL 4 - Design tokens (light theme)
# ═══════════════════════════════════════════════════════════════════════
BG = "#FAF8F3"
CARD_BG = "#FFFFFF"
TEXT = "#20262B"
SUBTEXT = "#77705F"
BORDER = "#E4DFD2"

HAZARD = "#C1622D"
RISK = "#33415C"
MITIGATION = "#1F7A5C"
VULNERABILITY = "#B8863B"
CATEGORY_COLORS = {
    "Hazard": HAZARD,
    "Risk": RISK,
    "Mitigation": MITIGATION,
    "Vulnerability": VULNERABILITY,
}

COMPANY_COLORS = {
    "Adobe": RISK,
    "Cognizant": HAZARD,
    "Accenture": MITIGATION,
    "Alphabet": VULNERABILITY,
    "Microsoft": "#7A4C7E",
}

FONT_HEAD = "IBM Plex Serif, Georgia, serif"
FONT_BODY = "IBM Plex Sans, Helvetica Neue, sans-serif"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=FONT_BODY, color=TEXT, size=12),
    margin=dict(l=50, r=40, t=56, b=40),
    bargap=0.32,
    bargroupgap=0.12,
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color=SUBTEXT, size=11),
        orientation="h",
        yanchor="top",
        y=-0.2,
        xanchor="center",
        x=0.5,
    ),
    xaxis=dict(showgrid=False, color=SUBTEXT, tickfont=dict(color=SUBTEXT), linecolor=BORDER, zeroline=False, automargin=True),
    yaxis=dict(showgrid=True, gridcolor=BORDER, color=SUBTEXT, tickfont=dict(color=SUBTEXT), linecolor="rgba(0,0,0,0)", zeroline=False, automargin=True),
    hoverlabel=dict(bgcolor=CARD_BG, bordercolor=BORDER, font=dict(family=FONT_BODY, color=TEXT)),
    transition=dict(duration=450, easing="cubic-in-out"),
)

# horizontal bar charts need the grid on the value axis (x), not the category axis (y),
# otherwise you get a row of pointless horizontal lines instead of readable value gridlines
PLOTLY_LAYOUT_HBAR = dict(PLOTLY_LAYOUT)
PLOTLY_LAYOUT_HBAR["xaxis"] = dict(showgrid=True, gridcolor=BORDER, color=SUBTEXT, tickfont=dict(color=SUBTEXT), linecolor="rgba(0,0,0,0)", zeroline=False, automargin=True)
PLOTLY_LAYOUT_HBAR["yaxis"] = dict(showgrid=False, color=TEXT, tickfont=dict(color=TEXT, size=12), linecolor=BORDER, zeroline=False, automargin=True)

HERO_IMAGE = "https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?w=1800&q=80&auto=format&fit=crop"

# ═══════════════════════════════════════════════════════════════════════
# CELL 5 - Figure builders (all take a filtered frame, called from callbacks)
# ═══════════════════════════════════════════════════════════════════════

def fig_empty(title, message="No data for the current company selection"):
    fig = go.Figure()
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=220,
                       title=dict(text=title, font=dict(color=TEXT, size=15, family=FONT_HEAD)))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(text=message, showarrow=False, font=dict(color=SUBTEXT, size=13))
    return fig


def fig_category_composition(filtered_cat_long, categories_selected):
    d = filtered_cat_long[filtered_cat_long["category"].isin(categories_selected)]
    if d.empty:
        return fig_empty("Where the disclosure weight sits")
    counts = d.groupby(["Company", "category"]).size().unstack(fill_value=0)
    counts = counts.reindex(columns=[c for c in CATEGORIES if c in counts.columns])
    fig = go.Figure()
    for cat in counts.columns:
        fig.add_trace(
            go.Bar(
                x=counts.index,
                y=counts[cat],
                name=cat,
                marker_color=CATEGORY_COLORS[cat],
                hovertemplate=f"<b>{cat}</b><br>%{{x}}: %{{y}} tagged chunks<extra></extra>",
            )
        )
    fig.update_layout(**PLOTLY_LAYOUT, barmode="stack", showlegend=True, yaxis_title="Tagged chunks",
                       title=dict(text="Where the disclosure weight sits", font=dict(color=TEXT, size=15, family=FONT_HEAD)))
    return fig


def fig_answer_type(filtered):
    if filtered.empty:
        return fig_empty("How complete, how quantitative")
    ct = pd.crosstab(filtered["Company"], filtered["Answer Type"], normalize="index") * 100
    for col in ["Quantitative", "Qualitative", "Not Applicable"]:
        if col not in ct.columns:
            ct[col] = 0
    ct = ct[["Quantitative", "Qualitative", "Not Applicable"]]
    colors = {"Quantitative": MITIGATION, "Qualitative": "#9A9384", "Not Applicable": HAZARD}
    fig = go.Figure()
    for col in ct.columns:
        fig.add_trace(
            go.Bar(
                x=ct.index, y=ct[col], name=col, marker_color=colors[col],
                hovertemplate=f"<b>{col}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
            )
        )
    fig.update_layout(**PLOTLY_LAYOUT, barmode="stack", showlegend=True, yaxis_title="Share of disclosures (%)",
                       title=dict(text="How complete, how quantitative", font=dict(color=TEXT, size=15, family=FONT_HEAD)))
    return fig


def fig_keyword_bar(df, title):
    if df.empty or df["Mentions"].sum() == 0:
        return fig_empty(title, "No keyword matches for the current company selection")
    d = df.sort_values("Mentions", ascending=True)
    fig = go.Figure(
        go.Bar(
            x=d["Mentions"], y=d["Company"], orientation="h",
            marker_color=[COMPANY_COLORS.get(c, RISK) for c in d["Company"]],
            text=d["Mentions"], textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x} mentions<extra></extra>",
        )
    )
    max_val = max(int(d["Mentions"].max()), 1)
    fig.update_layout(**PLOTLY_LAYOUT_HBAR, xaxis_title="Keyword mentions in extracted text",
                       title=dict(text=title, font=dict(color=TEXT, size=15, family=FONT_HEAD)),
                       height=90 + 42 * len(d))
    fig.update_xaxes(range=[0, max_val * 1.22])
    return fig


def fig_financial_risk(fin_df):
    d = fin_df[fin_df["Metric"] == "Cost of response to risk"].copy() if not fin_df.empty else fin_df
    if d.empty:
        return fig_empty("Disclosed cost of climate risk response",
                          "No company in the current selection discloses this figure")
    d = d.sort_values("Amount", ascending=True).reset_index(drop=True)
    fig = go.Figure(
        go.Bar(
            x=d["Company"], y=d["Amount"],
            marker_color=[COMPANY_COLORS.get(c, RISK) for c in d["Company"]],
            text=[f"${v:,.0f}" for v in d["Amount"]], textposition="outside", cliponaxis=False,
            width=0.4 if len(d) <= 2 else None,
            hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, yaxis_title="Reported cost (USD, log scale)",
                       yaxis_type="log",
                       title=dict(text="Disclosed cost of climate risk response", font=dict(color=TEXT, size=15, family=FONT_HEAD)))
    return fig


# ═══════════════════════════════════════════════════════════════════════
# CELL 6 - Helper UI components
# ═══════════════════════════════════════════════════════════════════════

def kpi_card(kpi_id, label, color):
    return html.Div(
        [
            html.P(label, style={"color": SUBTEXT, "fontSize": "11px", "letterSpacing": "1.5px",
                                  "textTransform": "uppercase", "margin": "0 0 8px 0", "fontFamily": FONT_BODY}),
            html.Span("0", id=kpi_id, style={"color": color, "fontSize": "32px", "fontWeight": "700",
                                              "fontFamily": FONT_HEAD, "lineHeight": "1"}),
        ],
        className="metric-card",
        style={"background": CARD_BG, "border": f"1px solid {BORDER}", "borderTop": f"2px solid {color}",
               "borderRadius": "8px", "padding": "20px", "flex": "1", "minWidth": "180px"},
    )


def section_label(text):
    return html.P(text, style={"color": SUBTEXT, "fontSize": "10px", "letterSpacing": "3px",
                                "textTransform": "uppercase", "fontFamily": FONT_BODY, "marginBottom": "12px",
                                "borderLeft": f"2px solid {MITIGATION}", "paddingLeft": "10px"})


def section_title(text):
    return html.H2(text, style={"color": TEXT, "fontFamily": FONT_HEAD, "fontSize": "27px",
                                 "fontWeight": "500", "margin": "0 0 28px 0"})


def chart_card(figure, gid=None):
    kwargs = {"figure": figure, "config": {"displayModeBar": False}}
    if gid:
        kwargs["id"] = gid
    return html.Div(dcc.Graph(**kwargs), className="metric-card",
                     style={"background": CARD_BG, "borderRadius": "8px", "padding": "8px", "border": f"1px solid {BORDER}"})


def data_table(table_id, columns, data):
    return dash_table.DataTable(
        id=table_id,
        columns=[{"name": c, "id": c} for c in columns],
        data=data,
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": "#F1EDE3", "color": TEXT, "fontFamily": FONT_BODY,
                      "fontWeight": "600", "fontSize": "12px", "border": f"1px solid {BORDER}", "textAlign": "left"},
        style_cell={"backgroundColor": CARD_BG, "color": TEXT, "fontFamily": FONT_BODY, "fontSize": "12px",
                    "border": f"1px solid {BORDER}", "textAlign": "left", "whiteSpace": "normal",
                    "height": "auto", "padding": "10px", "maxWidth": "360px"},
        style_data_conditional=[{"if": {"state": "active"}, "backgroundColor": "#F6F1E4", "border": f"1px solid {MITIGATION}"}],
        page_size=8,
    )


def note(text):
    return html.P(text, style={"color": SUBTEXT, "fontSize": "13px", "marginTop": "14px",
                                "fontFamily": FONT_BODY, "lineHeight": "1.7", "maxWidth": "820px"})


def explainer(text):
    """Sits right under the section title, before the chart or table.
    Answers 'what am I looking at' in one or two plain sentences."""
    return html.P(text, style={"color": TEXT, "fontSize": "13.5px", "marginBottom": "16px",
                                "fontFamily": FONT_BODY, "lineHeight": "1.65", "maxWidth": "820px",
                                "background": "#F6F3EA", "borderLeft": f"3px solid {MITIGATION}",
                                "padding": "10px 14px", "borderRadius": "3px"})


def unavailable_block(text):
    """For a question that genuinely cannot be answered from this file at all."""
    return html.Div(
        html.P(text, style={"color": TEXT, "fontSize": "14px", "fontFamily": FONT_BODY,
                             "lineHeight": "1.7", "margin": "0"}),
        style={"background": "#FBEEE6", "border": f"1px solid {HAZARD}", "borderLeft": f"4px solid {HAZARD}",
               "borderRadius": "6px", "padding": "20px 24px"},
    )


# ═══════════════════════════════════════════════════════════════════════
# CELL 7 - App & layout
# ═══════════════════════════════════════════════════════════════════════
app = Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap",
])

app.index_string = """
<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>CDP Five Company Dashboard</title>
{%favicon%}
{%css%}
<style>
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body { background: #FAF8F3; margin: 0; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #FAF8F3; }
    ::-webkit-scrollbar-thumb { background: #E4DFD2; border-radius: 3px; }
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
    .fade-section { animation: fadeInUp 0.7s ease both; }
    .metric-card { transition: transform 0.25s ease, box-shadow 0.25s ease; }
    .metric-card:hover { transform: translateY(-3px); box-shadow: 0 10px 24px rgba(32,38,43,0.08); }
    .filter-btn { transition: background 0.2s ease, color 0.2s ease; cursor: pointer; }
    .filter-btn:hover { opacity: 0.85; }
</style>
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
"""

# ── LANDING ──────────────────────────────────────────────────
landing = html.Div(
    id="landing",
    style={
        "minHeight": "88vh", "backgroundImage": f"url({HERO_IMAGE})", "backgroundSize": "cover",
        "backgroundPosition": "center 55%", "position": "relative", "display": "flex",
        "alignItems": "center", "justifyContent": "center", "flexDirection": "column", "textAlign": "center",
    },
    children=[
        html.Div(style={"position": "absolute", "inset": "0",
                         "background": "linear-gradient(to bottom, rgba(250,248,243,0.25) 0%, rgba(250,248,243,0.88) 68%, rgba(250,248,243,1) 100%)",
                         "zIndex": "0"}),
        html.Div(style={"position": "relative", "zIndex": "1", "padding": "0 20px"}, className="fade-section", children=[
            html.P("TISS Mumbai · BS Analytics & Sustainability Studies", style={
                "color": SUBTEXT, "fontSize": "11px", "letterSpacing": "3px", "textTransform": "uppercase",
                "fontFamily": FONT_BODY, "marginBottom": "22px"}),
            html.H1("Five Companies, One Reporting Cycle", style={
                "color": TEXT, "fontFamily": FONT_HEAD, "fontSize": "clamp(32px, 6vw, 66px)",
                "fontWeight": "600", "letterSpacing": "-1px", "margin": "0 0 16px 0", "lineHeight": "1.05"}),
            html.P("CDP Climate Change 2024 · Adobe, Cognizant, Accenture, Alphabet, Microsoft", style={
                "color": SUBTEXT, "fontFamily": FONT_BODY, "fontSize": "clamp(13px, 1.6vw, 17px)",
                "fontWeight": "400", "marginBottom": "40px"}),
            html.A("See the data ↓", href="#dashboard", className="filter-btn", style={
                "display": "inline-block", "background": MITIGATION, "color": "#FFFFFF",
                "padding": "13px 36px", "borderRadius": "3px", "fontSize": "13px", "letterSpacing": "2px",
                "textTransform": "uppercase", "textDecoration": "none", "fontFamily": FONT_BODY, "fontWeight": "500"}),
        ]),
        html.P("Photo - Andreas Gücklhorn on Unsplash", style={
            "position": "absolute", "bottom": "14px", "right": "18px", "color": SUBTEXT,
            "fontSize": "10px", "fontFamily": FONT_BODY, "zIndex": "1"}),
    ],
)

filter_panel = html.Div(style={"background": CARD_BG, "border": f"1px solid {BORDER}", "borderRadius": "8px",
                                "padding": "22px 28px", "marginBottom": "32px"}, children=[
    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                     "flexWrap": "wrap", "gap": "12px", "marginBottom": "14px"}, children=[
        html.P("FILTER BY COMPANY - pick one, a few, or all", style={
            "color": SUBTEXT, "fontSize": "9px", "letterSpacing": "3px", "fontFamily": FONT_BODY, "margin": "0"}),
        html.Div([
            html.Button("All", id="btn-all", n_clicks=0, className="filter-btn", style={
                "background": MITIGATION, "color": "#fff", "border": "none", "borderRadius": "3px",
                "padding": "6px 16px", "fontSize": "11px", "fontFamily": FONT_BODY, "marginRight": "8px"}),
            html.Button("Clear", id="btn-clear", n_clicks=0, className="filter-btn", style={
                "background": "#EDE8DC", "color": TEXT, "border": "none", "borderRadius": "3px",
                "padding": "6px 16px", "fontSize": "11px", "fontFamily": FONT_BODY}),
        ]),
    ]),
    dcc.Checklist(
        id="company-filter",
        options=[{"label": f" {c}", "value": c} for c in COMPANIES],
        value=COMPANIES,
        inline=True,
        style={"fontFamily": FONT_BODY, "fontSize": "13px", "color": TEXT},
        inputStyle={"marginRight": "6px", "marginLeft": "14px"},
    ),
])

dashboard = html.Div(id="dashboard", style={"padding": "70px 5% 40px", "maxWidth": "1360px", "margin": "0 auto"}, children=[
    section_label("Reframed from the assignment brief - company replaces year as the comparison axis"),
    section_title("Disclosure at a glance"),

    html.Div(style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "32px"}, children=[
        kpi_card("kpi-total-value", "Tagged disclosures in view", RISK),
        kpi_card("kpi-companies-value", "Companies selected", MITIGATION),
        kpi_card("kpi-pct-value", "Share quantitative", HAZARD),
        kpi_card("kpi-categories-value", "Categories touched", VULNERABILITY),
    ]),

    filter_panel,

    html.Div(style={"marginBottom": "56px"}, className="fade-section", children=[
        section_label("Question 1, reframed · not answerable year over year, this file has one year"),
        section_title("Where the disclosure weight sits"),
        explainer("Counts how many extracted chunks were tagged Hazard, Risk, Mitigation, or Vulnerability, "
                  "per company. A taller bar means more of that company's report matched that language, not "
                  "more real-world exposure."),
        html.Div(style={"display": "flex", "gap": "12px", "marginBottom": "14px", "flexWrap": "wrap"}, children=[
            dcc.Checklist(id="category-filter", options=[{"label": f" {c}", "value": c} for c in CATEGORIES],
                          value=CATEGORIES, inline=True,
                          style={"fontFamily": FONT_BODY, "fontSize": "12px", "color": SUBTEXT},
                          inputStyle={"marginRight": "5px", "marginLeft": "12px"}),
        ]),
        chart_card(fig_category_composition(cat_long, CATEGORIES), gid="chart-category"),
        note("Each company's CDP response was chunked by page and tagged wherever hazard, risk, mitigation or "
             "vulnerability language showed up. Risk dominates across the board because the CDP Climate Change "
             "questionnaire itself is risk-heavy in structure, not because these five companies are unusually "
             "exposed. Read the bar heights as reporting emphasis, not real-world risk."),
    ]),

    html.Div(style={"marginBottom": "56px"}, className="fade-section", children=[
        section_label("Questions 3 and 4, reframed · completeness and quantitative depth, company vs company"),
        section_title("How complete, how quantitative"),
        explainer("Shows what share of each company's tagged chunks are Quantitative, Qualitative, or Not "
                  "Applicable (the closest thing this file has to a blank answer). A bigger green segment "
                  "means more numbers-backed disclosure."),
        chart_card(fig_answer_type(raw), gid="chart-answertype"),
        note("Not Applicable means the extractor found no text under that question code, so it is the closest "
             "proxy this file has for a blank response. Quantitative share is a rough read on how numbers-backed "
             "a company's disclosure is. All five sit mostly in qualitative territory; nobody here is reporting "
             "mostly hard numbers."),
    ]),

    html.Div(style={"marginBottom": "56px"}, className="fade-section", children=[
        section_label("Question 5, reframed · copy paste check within a single report, not across years"),
        section_title("Repeated question codes"),
        explainer("Lists every question code a company answered more than once, and checks whether the "
                  "repeated text is identical. If the table is empty for your selection, none of the "
                  "companies you picked have a question code that repeats."),
        html.Div(id="table-repeats"),
        note("Some CDP question codes get answered more than once inside a single company's report, usually "
             "because the form has repeatable rows for separate risks or separate environmental issues. This "
             "table checks whether those repeats carry identical text, which would flag boilerplate rather than "
             "fresh content. A 'different content' row is normal and expected; an 'identical text' row is worth "
             "a second look."),
    ]),

    html.Div(style={"marginBottom": "56px"}, className="fade-section", children=[
        section_label("Question 6 · not reframed, not answerable, shown here instead of quietly left out"),
        section_title("Basic facts moving plausibly year to year"),
        unavailable_block(
            "This question checks whether numbers that should barely change, population, jurisdiction area, "
            "move by a believable amount from one year to the next, as a sanity check against data entry "
            "errors. It cannot be answered here, for two separate reasons. First, companies do not have a "
            "population or a jurisdiction area, that concept belongs to the city version of this brief. "
            "Second, even if a company-equivalent metric existed, this file is one reporting cycle, so there "
            "is no second year to check it against. Swapping company in for year, the fix used everywhere "
            "else in this dashboard, does not rescue this one. The question needs a time axis this file does "
            "not have. This is the one question left as a straight no rather than a reframe."
        ),
    ]),

    html.Div(style={"marginBottom": "56px"}, className="fade-section", children=[
        section_label("Question 7, reframed · what gets left blank, company vs company instead of year vs year"),
        section_title("Where the extraction came up empty"),
        explainer("Every chunk tagged Not Applicable, meaning no text was found under that question code, "
                  "for the companies you have selected. An empty table below means no blanks turned up for "
                  "this selection, not that the search failed."),
        html.Div(id="table-blanks"),
        html.Div(id="blank-callout"),
        note("Only five chunks in the whole file are tagged Not Applicable, so treat this as a small-sample "
             "observation, not a firm pattern."),
    ]),

    html.Div(style={"marginBottom": "56px"}, className="fade-section", children=[
        section_label("Question 2, reframed · targets stated this cycle, not tracked across cycles"),
        section_title("Stated climate targets"),
        explainer("Counts mentions of target language (net zero, science based targets, RE100, target years) "
                  "per company, chart first, then the matched terms and one example excerpt per company in "
                  "the table below."),
        chart_card(fig_keyword_bar(scan_keywords(raw, TARGET_KEYWORDS), "Target-related mentions by company"), gid="chart-targets"),
        html.Div(id="table-targets"),
        note("Counted by keyword match against terms like science based target, net zero, RE100 and target "
             "years. This counts mentions, not verified commitments. A high count means the report talks about "
             "targets often, not that the target is ambitious or on track."),
    ]),

    html.Div(style={"marginBottom": "56px"}, className="fade-section", children=[
        section_label("Question 8, reframed · who owns this on paper right now, not how it changed"),
        section_title("Named climate governance"),
        explainer("Counts mentions of governance titles and bodies (board of directors, audit committee, "
                  "chief sustainability officer, and similar) per company, with one example excerpt each. "
                  "Zero mentions means that title did not turn up in this company's extracted text, not "
                  "that nobody is responsible."),
        html.Div(id="table-governance"),
        note("This is a single snapshot. Without a prior year of this same file there is no way to say whether "
             "ownership shifted, so this table only shows who is named as responsible in the current report."),
    ]),

    html.Div(style={"marginBottom": "56px"}, className="fade-section", children=[
        section_label("Question 9, reframed · policy engagement mentioned, not tracked over time"),
        section_title("Government and policy engagement"),
        explainer("Counts mentions of regulator, policy advocacy, and legislation language per company, "
                  "with one example excerpt each. This is presence in this cycle's text, not a measure of "
                  "how the engagement has changed."),
        html.Div(id="table-policy"),
        note("No count here means that company's extracted text did not contain any of the scanned policy "
             "terms, it does not mean the company has no government relations activity, only that this "
             "keyword pass did not catch it."),
    ]),

    html.Div(style={"marginBottom": "56px"}, className="fade-section", children=[
        section_label("Question 10, reframed · financing mechanisms named this cycle"),
        section_title("Climate financing signals"),
        explainer("Counts mentions of concrete financing mechanisms (green bonds, CAPEX or OPEX tied to "
                  "climate, credit rating links) per company. Short bars are not a search failure, most of "
                  "these five companies simply do not name specific financing mechanisms in what got extracted."),
        chart_card(fig_keyword_bar(scan_keywords(raw, FINANCE_KEYWORDS), "Financing mentions by company"), gid="chart-financing"),
        note("Green bonds, sustainability-linked terms, CAPEX or OPEX tied to climate, credit rating links. "
             "Most bars here are at or near zero. That is the finding: concrete financing mechanisms are barely "
             "disclosed by four of these five companies in what got extracted, not a gap in the search."),
    ]),

    html.Div(style={"marginBottom": "40px"}, className="fade-section", children=[
        section_label("Question 11, reframed · disclosed figures compared across companies, not across years"),
        section_title("Cost of climate risk response"),
        explainer("Compares the one dollar figure most of these companies actually disclose: what it costs "
                  "them to respond to a named climate risk. Only companies with an extractable figure show "
                  "up as bars, the rest are explained in the note below the chart, not silently dropped."),
        chart_card(fig_financial_risk(extract_financial_figures(raw)), gid="chart-financial"),
        note("Log scale because Adobe discloses a $375,000 response cost and Alphabet discloses $16,000,000 for "
             "the same line item, and a linear axis would flatten one of them to nothing. Cognizant has a "
             "matching question code answered but with no extractable figure in the text. Accenture and "
             "Microsoft do not have this question code tagged at all in the extraction."),
    ]),
])

closing = html.Div(style={"background": "#F1EDE3", "borderTop": f"2px solid {BORDER}", "padding": "70px 5%"}, children=[
    html.Div(style={"maxWidth": "1100px", "margin": "0 auto"}, children=[
        section_label("Read this before you write up any findings"),
        section_title("How the brief's eleven questions were actually handled"),
        data_table(
            "table-methodology",
            ["#", "Original question (short form)", "What this dashboard does with it"],
            [
                {"#": "1", "Original question (short form)": "Hazard count/severity trend across years",
                 "What this dashboard does with it": "Reframed: category composition compared across companies"},
                {"#": "2", "Original question (short form)": "Targets met, revised, delayed, dropped across years",
                 "What this dashboard does with it": "Reframed: target keyword mentions this cycle only, no tracking"},
                {"#": "3", "Original question (short form)": "Completeness improving in later years",
                 "What this dashboard does with it": "Reframed: Not Applicable share compared across companies"},
                {"#": "4", "Original question (short form)": "Shift toward quantitative disclosure over years",
                 "What this dashboard does with it": "Reframed: quantitative share compared across companies"},
                {"#": "5", "Original question (short form)": "Identical answers repeated year after year",
                 "What this dashboard does with it": "Reframed: identical text across repeated codes within one report"},
                {"#": "6", "Original question (short form)": "Basic facts (population, jurisdiction area) moving plausibly",
                 "What this dashboard does with it": "Not answerable, given its own section above explaining why, instead of being left out"},
                {"#": "7", "Original question (short form)": "Questions consistently left blank across years",
                 "What this dashboard does with it": "Reframed: Not Applicable codes shared across more than one company"},
                {"#": "8", "Original question (short form)": "Reporting ownership shifting departments over years",
                 "What this dashboard does with it": "Reframed: named governance owners this cycle, single snapshot"},
                {"#": "9", "Original question (short form)": "Government engagement changing in intensity over years",
                 "What this dashboard does with it": "Reframed: policy engagement mentions this cycle, single snapshot"},
                {"#": "10", "Original question (short form)": "Financing strategy evolving over years",
                 "What this dashboard does with it": "Reframed: financing mechanism mentions this cycle, single snapshot"},
                {"#": "11", "Original question (short form)": "Financial impact estimates growing or shrinking across years",
                 "What this dashboard does with it": "Reframed: disclosed risk-response figures compared across companies"},
            ],
        ),
        html.Div(style={"marginTop": "36px", "borderTop": f"1px solid {BORDER}", "paddingTop": "24px"}, children=[
            html.P("Data source and method", style={"color": TEXT, "fontFamily": FONT_HEAD, "fontSize": "15px", "marginBottom": "10px"}),
            html.P("Companies_CDP_MERGED.xlsx - CDP Climate Change 2024 questionnaire responses for five "
                   "companies, extracted at the page/question chunk level and tagged Hazard, Risk, Mitigation "
                   "or Vulnerability where that language appears. Start Page ranges in the source file are "
                   "non-overlapping per company, which is how the five reports were told apart after merging.",
                   style={"color": SUBTEXT, "fontSize": "11px", "fontFamily": FONT_BODY, "margin": "3px 0", "lineHeight": "1.7"}),
            html.P("Keyword scans (targets, governance, policy, financing) and the currency figure extraction "
                   "are regex-based against the raw extracted text. They are a reasonable first pass, not a "
                   "verified audit. Treat every count here as a floor, not a ceiling.",
                   style={"color": SUBTEXT, "fontSize": "11px", "fontFamily": FONT_BODY, "margin": "3px 0", "lineHeight": "1.7"}),
            html.Div(style={"marginTop": "18px", "paddingTop": "18px", "borderTop": f"1px solid {BORDER}"}, children=[
                html.P("BS in Analytics and Sustainability Studies (2024–28) · TISS Mumbai",
                       style={"color": SUBTEXT, "fontSize": "10px", "fontFamily": FONT_BODY, "letterSpacing": "0.5px"}),
            ]),
        ]),
    ])
])

app.layout = html.Div(style={"backgroundColor": BG, "fontFamily": FONT_BODY}, children=[
    landing,
    dashboard,
    closing,
    dcc.Store(id="kpi-target-store"),
    dcc.Interval(id="kpi-interval", interval=25, n_intervals=0, max_intervals=30),
])

# ═══════════════════════════════════════════════════════════════════════
# CELL 8 - Callbacks
# ═══════════════════════════════════════════════════════════════════════

@app.callback(Output("company-filter", "value"), Input("btn-all", "n_clicks"),
              Input("btn-clear", "n_clicks"), prevent_initial_call=True)
def toggle_companies(all_clicks, clear_clicks):
    from dash import ctx
    trigger = ctx.triggered_id
    if trigger == "btn-all":
        return COMPANIES
    return []


@app.callback(
    Output("chart-category", "figure"),
    Input("company-filter", "value"),
    Input("category-filter", "value"),
)
def update_category_chart(selected_companies, selected_categories):
    selected_companies = selected_companies or []
    selected_categories = selected_categories or CATEGORIES
    d = cat_long[cat_long["Company"].isin(selected_companies)]
    return fig_category_composition(d, selected_categories)


@app.callback(
    Output("chart-answertype", "figure"),
    Output("table-repeats", "children"),
    Output("table-blanks", "children"),
    Output("blank-callout", "children"),
    Output("chart-targets", "figure"),
    Output("table-targets", "children"),
    Output("table-governance", "children"),
    Output("table-policy", "children"),
    Output("chart-financing", "figure"),
    Output("chart-financial", "figure"),
    Output("kpi-target-store", "data"),
    Output("kpi-interval", "n_intervals"),
    Input("company-filter", "value"),
)
def update_everything(selected_companies):
    selected_companies = selected_companies or []
    filtered = raw[raw["Company"].isin(selected_companies)]

    # KPI targets
    n_categories = 0
    if not filtered.empty:
        n_categories = filtered.assign(category=filtered["Matched Category"].str.split(", ")).explode("category")["category"].nunique()
    pct_quant = 0.0
    if not filtered.empty:
        pct_quant = (filtered["Answer Type"] == "Quantitative").mean() * 100
    kpi_targets = {
        "total": int(len(filtered)),
        "companies": int(len(selected_companies)),
        "pct_quant": float(round(pct_quant, 1)),
        "categories": int(n_categories),
    }

    # answer type
    fig_at = fig_answer_type(filtered)

    # repeats table
    rep_df = repeated_code_table(filtered)
    if rep_df.empty:
        rep_table = html.P("No repeated question codes in this selection.", style={"color": SUBTEXT, "fontFamily": FONT_BODY, "fontSize": "13px"})
    else:
        rep_table = data_table("tbl-repeats", rep_df.columns.tolist(), rep_df.to_dict("records"))

    # blanks table + callout
    blanks = filtered[filtered["Answer Type"] == "Not Applicable"][["Company", "Question Code", "Matched Category", "Start Page"]].rename(columns={"Matched Category": "Category"})
    if blanks.empty:
        blanks_table = html.P("No Not Applicable chunks in this selection.", style={"color": SUBTEXT, "fontFamily": FONT_BODY, "fontSize": "13px"})
        callout = ""
    else:
        blanks_table = data_table("tbl-blanks", blanks.columns.tolist(), blanks.to_dict("records"))
        shared = blanks.groupby("Question Code")["Company"].nunique()
        shared = shared[shared > 1]
        if len(shared) > 0:
            codes = ", ".join(shared.index.tolist())
            companies_involved = ", ".join(sorted(blanks[blanks["Question Code"].isin(shared.index)]["Company"].unique()))
            callout = html.P(f"Question code {codes} comes up blank for more than one company in this selection ({companies_involved}). "
                              f"That is either a genuinely skipped question for this sector or an extraction miss worth checking against the source PDF.",
                              style={"color": HAZARD, "fontSize": "12px", "fontFamily": FONT_BODY, "fontWeight": "500", "marginTop": "10px"})
        else:
            callout = ""

    # targets
    target_df = scan_keywords(filtered, TARGET_KEYWORDS)
    fig_targets = fig_keyword_bar(target_df, "Target-related mentions by company")
    targets_table = data_table("tbl-targets", target_df.columns.tolist(), target_df.to_dict("records"))

    # governance
    gov_df = scan_keywords(filtered, GOV_KEYWORDS)
    gov_table = data_table("tbl-gov", gov_df.columns.tolist(), gov_df.to_dict("records"))

    # policy
    policy_df = scan_keywords(filtered, POLICY_KEYWORDS)
    policy_table = data_table("tbl-policy", policy_df.columns.tolist(), policy_df.to_dict("records"))

    # financing
    finance_df = scan_keywords(filtered, FINANCE_KEYWORDS)
    fig_financing = fig_keyword_bar(finance_df, "Financing mentions by company")

    # financial risk figures
    fig_financial = fig_financial_risk(extract_financial_figures(filtered))

    return (fig_at, rep_table, blanks_table, callout, fig_targets, targets_table,
            gov_table, policy_table, fig_financing, fig_financial, kpi_targets, 0)


app.clientside_callback(
    """
    function(n_intervals, targets) {
        if (!targets) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update,
                    window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        const progress = Math.min(1, n_intervals / 28);
        const eased = 1 - Math.pow(1 - progress, 3);
        function fmtInt(target) { return Math.round(target * eased).toLocaleString(); }
        function fmtPct(target) { return (target * eased).toFixed(1) + '%'; }
        return [fmtInt(targets.total), fmtInt(targets.companies), fmtPct(targets.pct_quant), fmtInt(targets.categories)];
    }
    """,
    Output("kpi-total-value", "children"),
    Output("kpi-companies-value", "children"),
    Output("kpi-pct-value", "children"),
    Output("kpi-categories-value", "children"),
    Input("kpi-interval", "n_intervals"),
    State("kpi-target-store", "data"),
)

# ═══════════════════════════════════════════════════════════════════════
# CELL 9 - Run
# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=False, port=8050)
