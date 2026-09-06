"""
utils/visuals.py
-----------------
Bouwt alle interactieve grafieken (Plotly). Kleuren en fonts komen uit
utils/parameters.py, zodat de huisstijl van het rapport op 1 plek staat.
"""

import pandas as pd
import plotly.graph_objects as go

from utils import parameters as p

BASE_LAYOUT = dict(
    font=dict(family=p.FONT_SANS, size=13, color=p.INK),
    paper_bgcolor=p.PAPER,
    plot_bgcolor=p.PAPER,
    margin=dict(l=56, r=24, t=24, b=44),
    hoverlabel=dict(
        bgcolor=p.INK, font_color=p.PAPER, font_family=p.FONT_SANS, font_size=12,
        bordercolor=p.INK,
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                font=dict(size=12)),
    xaxis=dict(showgrid=False, showline=True, linecolor=p.GRID, ticks="outside",
               tickcolor=p.GRID, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor=p.GRID, zeroline=False, ticks=""),
)


def _apply_base(fig: go.Figure, y_title: str = "") -> go.Figure:
    fig.update_layout(**BASE_LAYOUT)
    fig.update_yaxes(title=y_title)
    return fig


def fig_sterfte_drieluik(sterftetrends: pd.DataFrame) -> go.Figure:
    """Figuur met keuzeknoppen: absoluut / relatief / gestandaardiseerd (1950-2024)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sterftetrends["jaar"], y=sterftetrends["overledenen_x10000"],
        name="Absoluut (x 10.000)", line=dict(color=p.INK, width=2.5),
        hovertemplate="%{x}: %{y:.2f} (x 10.000)<extra></extra>", visible=True,
    ))
    fig.add_trace(go.Scatter(
        x=sterftetrends["jaar"], y=sterftetrends["overledenen_relatief"],
        name="Relatief (per 1.000 inwoners)", line=dict(color=p.TEAL, width=2.5),
        hovertemplate="%{x}: %{y:.1f} per 1.000<extra></extra>", visible=False,
    ))
    fig.add_trace(go.Scatter(
        x=sterftetrends["jaar"], y=sterftetrends["overledenen_gestandaardiseerd"],
        name="Gestandaardiseerd (naar bevolking 1990)", line=dict(color=p.GOLD, width=2.5),
        hovertemplate="%{x}: %{y:.1f} per 1.000<extra></extra>", visible=False,
    ))

    labels = ["Absoluut", "Relatief", "Gestandaardiseerd"]
    buttons = [
        dict(label=label, method="update", args=[{"visible": [j == i for j in range(3)]}])
        for i, label in enumerate(labels)
    ]

    fig.update_layout(
        updatemenus=[dict(
            type="buttons", direction="right", x=0, y=1.18, xanchor="left",
            showactive=True, buttons=buttons,
            font=dict(size=12), bgcolor=p.PAPER, bordercolor=p.GRID,
        )],
        showlegend=False,
    )
    _apply_base(fig, y_title="Aantal overledenen")
    return fig


def fig_gebeurtenissen_annotatie(sterftetrends: pd.DataFrame,
                                  gebeurtenissen: pd.DataFrame) -> go.Figure:
    """Gestandaardiseerde sterfte 2010-2024 met annotaties bij griep/corona-jaren."""
    df = sterftetrends[sterftetrends["jaar"] >= 2010]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["jaar"], y=df["overledenen_gestandaardiseerd"],
        line=dict(color=p.INK, width=2.5), mode="lines+markers",
        marker=dict(size=5, color=p.INK),
        hovertemplate="%{x}: %{y:.1f} per 1.000<extra></extra>", showlegend=False,
    ))

    for _, gebeurtenis in gebeurtenissen.iterrows():
        jaar = gebeurtenis["jaar"]
        rij = df[df["jaar"] == jaar]
        if rij.empty:
            continue
        y = rij["overledenen_gestandaardiseerd"].iloc[0]
        kleur = p.WINE if gebeurtenis["type"] == "covid" else p.GOLD
        fig.add_annotation(
            x=jaar, y=y, text=gebeurtenis["label"], showarrow=True,
            arrowhead=0, arrowcolor=kleur, ax=0, ay=-38,
            font=dict(size=11, color=kleur), bordercolor=kleur, borderwidth=1,
            borderpad=3, bgcolor=p.PAPER,
        )

    _apply_base(fig, y_title="Gestandaardiseerde sterfte (per 1.000)")
    return fig


def fig_scenario(scenario_df: pd.DataFrame) -> go.Figure:
    """Eigen toevoeging: werkelijke trend vs. geextrapoleerde pre-corona trend."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=scenario_df["jaar"], y=scenario_df["werkelijk"],
        name="Werkelijk", line=dict(color=p.INK, width=2.5),
        hovertemplate="%{x}: %{y:.2f} per 1.000 (werkelijk)<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=scenario_df["jaar"], y=scenario_df["verwacht_pre_corona_trend"],
        name="Verwacht bij doorzetten trend 2010-2019", mode="lines",
        line=dict(color=p.GOLD, width=2, dash="dash"),
        hovertemplate="%{x}: %{y:.2f} per 1.000 (scenario)<extra></extra>",
    ))
    na2019 = scenario_df[scenario_df["jaar"] >= 2019]
    fig.add_trace(go.Scatter(
        x=list(na2019["jaar"]) + list(na2019["jaar"][::-1]),
        y=list(na2019["werkelijk"]) + list(na2019["verwacht_pre_corona_trend"][::-1]),
        fill="toself", fillcolor="rgba(140,59,74,0.12)",
        line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip", showlegend=False,
    ))
    _apply_base(fig, y_title="Gestandaardiseerde sterfte (per 1.000)")
    return fig


def fig_levensverwachting(levensverwachting: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=levensverwachting["jaar"], y=levensverwachting["mannen"],
        name="Mannen", line=dict(color=p.TEAL, width=2.5),
        hovertemplate="%{x}: %{y:.2f} jaar<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=levensverwachting["jaar"], y=levensverwachting["vrouwen"],
        name="Vrouwen", line=dict(color=p.WINE, width=2.5),
        hovertemplate="%{x}: %{y:.2f} jaar<extra></extra>",
    ))
    _apply_base(fig, y_title="Levensverwachting bij geboorte (jaren)")
    return fig


def fig_leeftijdsopbouw(leeftijdsaandelen_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    reeksen = [
        ("leeftijd_0_65_aandeel", "0 tot 65 jaar", p.INK),
        ("leeftijd_65_80_aandeel", "65 tot 80 jaar", p.TEAL),
        ("leeftijd_80_plus_aandeel", "80 jaar of ouder", p.GOLD),
    ]
    for col, naam, kleur in reeksen:
        fig.add_trace(go.Scatter(
            x=leeftijdsaandelen_df["jaar"], y=leeftijdsaandelen_df[col] * 100,
            name=naam, stackgroup="one", line=dict(width=0.5, color=kleur),
            fillcolor=kleur, hovertemplate="%{x}: %{y:.1f}%%<extra></extra>",
        ))
    _apply_base(fig, y_title="Aandeel van totaal aantal overledenen (%)")
    fig.update_yaxes(range=[0, 100])
    return fig


def fig_eu_vergelijking(eu_df: pd.DataFrame) -> go.Figure:
    kleuren = [p.WINE if is_nl else "#C9C4B4" for is_nl in eu_df["is_nl"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=eu_df["jaar_2023"], y=eu_df["land"], orientation="h",
        marker=dict(color=kleuren),
        hovertemplate="%{y}: %{x:.1f} jaar<extra></extra>",
    ))
    fig.add_vline(x=eu_df["eu27_gemiddelde"].iloc[0], line_dash="dot",
                  line_color=p.MUTED,
                  annotation_text="EU-27 gemiddelde", annotation_position="top",
                  annotation_font_color=p.MUTED, annotation_font_size=11)
    fig.update_layout(**BASE_LAYOUT)
    fig.update_xaxes(title="Levensverwachting bij geboorte, 2023 (jaren)")
    fig.update_yaxes(title="", tickfont=dict(size=11))
    fig.update_layout(height=620, margin=dict(l=110, r=24, t=24, b=44))
    return fig
