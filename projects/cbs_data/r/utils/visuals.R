# utils/visuals.R
# --------------------------------------------------------------
# Bouwt de data/layout-specificaties voor elke grafiek als gewone R-lists,
# in exact dezelfde vorm als de Plotly JSON-structuur (dezelfde velden als
# de Python-versie, die plotly.graph_objects gebruikt). Bewust GEEN
# afhankelijkheid van het (zware) R-package `plotly`: report.R zet deze
# lists zelf om in de div/script-HTML die Plotly.js nodig heeft, met
# alleen jsonlite om te serialiseren. Zie utils/report.R::fig_to_html().

base_layout <- function(y_title = "") {
  yaxis <- list(showgrid = TRUE, gridcolor = GRID, zeroline = FALSE, ticks = "")
  if (nzchar(y_title)) yaxis$title <- y_title

  list(
    font = list(family = FONT_SANS, size = 13, color = INK),
    paper_bgcolor = PAPER,
    plot_bgcolor = PAPER,
    margin = list(l = 56, r = 24, t = 24, b = 44),
    hoverlabel = list(
      bgcolor = INK,
      font = list(color = PAPER, family = FONT_SANS, size = 12),
      bordercolor = INK
    ),
    legend = list(orientation = "h", yanchor = "bottom", y = 1.02, xanchor = "left", x = 0,
                  font = list(size = 12)),
    xaxis = list(showgrid = FALSE, showline = TRUE, linecolor = GRID, ticks = "outside",
                 tickcolor = GRID, zeroline = FALSE),
    yaxis = yaxis
  )
}

fig_sterfte_drieluik <- function(sterftetrends) {
  data <- list(
    list(x = sterftetrends$jaar, y = sterftetrends$overledenen_x10000, type = "scatter",
         mode = "lines", name = "Absoluut (x 10.000)",
         line = list(color = INK, width = 2.5),
         hovertemplate = "%{x}: %{y:.2f} (x 10.000)<extra></extra>", visible = TRUE),
    list(x = sterftetrends$jaar, y = sterftetrends$overledenen_relatief, type = "scatter",
         mode = "lines", name = "Relatief (per 1.000 inwoners)",
         line = list(color = TEAL, width = 2.5),
         hovertemplate = "%{x}: %{y:.1f} per 1.000<extra></extra>", visible = FALSE),
    list(x = sterftetrends$jaar, y = sterftetrends$overledenen_gestandaardiseerd, type = "scatter",
         mode = "lines", name = "Gestandaardiseerd (naar bevolking 1990)",
         line = list(color = GOLD, width = 2.5),
         hovertemplate = "%{x}: %{y:.1f} per 1.000<extra></extra>", visible = FALSE)
  )

  buttons <- list(
    list(label = "Absoluut", method = "update",
         args = list(list(visible = c(TRUE, FALSE, FALSE)))),
    list(label = "Relatief", method = "update",
         args = list(list(visible = c(FALSE, TRUE, FALSE)))),
    list(label = "Gestandaardiseerd", method = "update",
         args = list(list(visible = c(FALSE, FALSE, TRUE))))
  )

  layout <- base_layout("Aantal overledenen")
  layout$showlegend <- FALSE
  layout$updatemenus <- list(list(
    type = "buttons", direction = "right", x = 0, y = 1.18, xanchor = "left",
    showactive = TRUE, buttons = buttons,
    font = list(size = 12), bgcolor = PAPER, bordercolor = GRID
  ))

  list(data = data, layout = layout)
}

fig_gebeurtenissen_annotatie <- function(sterftetrends, gebeurtenissen) {
  df <- sterftetrends[sterftetrends$jaar >= 2010, ]

  data <- list(list(
    x = df$jaar, y = df$overledenen_gestandaardiseerd, type = "scatter",
    mode = "lines+markers", line = list(color = INK, width = 2.5),
    marker = list(size = 5, color = INK),
    hovertemplate = "%{x}: %{y:.1f} per 1.000<extra></extra>", showlegend = FALSE
  ))

  annotations <- list()
  for (i in seq_len(nrow(gebeurtenissen))) {
    jaar <- gebeurtenissen$jaar[i]
    rij <- df[df$jaar == jaar, ]
    if (nrow(rij) == 0) next
    y <- rij$overledenen_gestandaardiseerd[1]
    kleur <- if (gebeurtenissen$type[i] == "covid") WINE else GOLD
    annotations[[length(annotations) + 1]] <- list(
      x = jaar, y = y, text = gebeurtenissen$label[i], showarrow = TRUE,
      arrowhead = 0, arrowcolor = kleur, ax = 0, ay = -38,
      font = list(size = 11, color = kleur), bordercolor = kleur, borderwidth = 1,
      borderpad = 3, bgcolor = PAPER
    )
  }

  layout <- base_layout("Gestandaardiseerde sterfte (per 1.000)")
  layout$annotations <- annotations

  list(data = data, layout = layout)
}

fig_scenario <- function(scenario_df) {
  na2019 <- scenario_df[scenario_df$jaar >= 2019, ]

  data <- list(
    list(x = scenario_df$jaar, y = scenario_df$werkelijk, type = "scatter", mode = "lines",
         name = "Werkelijk", line = list(color = INK, width = 2.5),
         hovertemplate = "%{x}: %{y:.2f} per 1.000 (werkelijk)<extra></extra>"),
    list(x = scenario_df$jaar, y = scenario_df$verwacht_pre_corona_trend, type = "scatter",
         mode = "lines", name = "Verwacht bij doorzetten trend 2010-2019",
         line = list(color = GOLD, width = 2, dash = "dash"),
         hovertemplate = "%{x}: %{y:.2f} per 1.000 (scenario)<extra></extra>"),
    list(x = c(na2019$jaar, rev(na2019$jaar)),
         y = c(na2019$werkelijk, rev(na2019$verwacht_pre_corona_trend)),
         type = "scatter", fill = "toself", fillcolor = "rgba(140,59,74,0.12)",
         line = list(color = "rgba(0,0,0,0)"), hoverinfo = "skip", showlegend = FALSE)
  )

  list(data = data, layout = base_layout("Gestandaardiseerde sterfte (per 1.000)"))
}

fig_levensverwachting <- function(levensverwachting) {
  data <- list(
    list(x = levensverwachting$jaar, y = levensverwachting$mannen, type = "scatter",
         mode = "lines", name = "Mannen", line = list(color = TEAL, width = 2.5),
         hovertemplate = "%{x}: %{y:.2f} jaar<extra></extra>"),
    list(x = levensverwachting$jaar, y = levensverwachting$vrouwen, type = "scatter",
         mode = "lines", name = "Vrouwen", line = list(color = WINE, width = 2.5),
         hovertemplate = "%{x}: %{y:.2f} jaar<extra></extra>")
  )
  list(data = data, layout = base_layout("Levensverwachting bij geboorte (jaren)"))
}

fig_leeftijdsopbouw <- function(leeftijdsaandelen_df) {
  reeksen <- list(
    list(col = "leeftijd_0_65_aandeel",    naam = "0 tot 65 jaar",    kleur = INK),
    list(col = "leeftijd_65_80_aandeel",   naam = "65 tot 80 jaar",   kleur = TEAL),
    list(col = "leeftijd_80_plus_aandeel", naam = "80 jaar of ouder", kleur = GOLD)
  )

  data <- lapply(reeksen, function(r) list(
    x = leeftijdsaandelen_df$jaar,
    y = leeftijdsaandelen_df[[r$col]] * 100,
    type = "scatter", stackgroup = "one",
    name = r$naam,
    line = list(width = 0.5, color = r$kleur),
    fillcolor = r$kleur,
    hovertemplate = "%{x}: %{y:.1f}%<extra></extra>"
  ))

  layout <- base_layout("Aandeel van totaal aantal overledenen (%)")
  layout$yaxis$range <- c(0, 100)

  list(data = data, layout = layout)
}

fig_eu_vergelijking <- function(eu_df) {
  kleuren <- ifelse(eu_df$is_nl, WINE, "#C9C4B4")

  data <- list(list(
    x = eu_df$jaar_2023, y = eu_df$land, type = "bar", orientation = "h",
    marker = list(color = kleuren),
    hovertemplate = "%{y}: %{x:.1f} jaar<extra></extra>"
  ))

  layout <- base_layout()
  layout$xaxis$title <- "Levensverwachting bij geboorte, 2023 (jaren)"
  layout$yaxis <- list(title = "", tickfont = list(size = 11))
  layout$height <- 620
  layout$margin <- list(l = 110, r = 24, t = 24, b = 44)
  layout$shapes <- list(list(
    type = "line", x0 = eu_df$eu27_gemiddelde[1], x1 = eu_df$eu27_gemiddelde[1],
    xref = "x", y0 = 0, y1 = 1, yref = "y domain",
    line = list(color = MUTED, dash = "dot")
  ))
  layout$annotations <- list(list(
    x = eu_df$eu27_gemiddelde[1], y = 1, xref = "x", yref = "y domain",
    xanchor = "center", yanchor = "bottom", showarrow = FALSE,
    text = "EU-27 gemiddelde", font = list(color = MUTED, size = 11)
  ))

  list(data = data, layout = layout)
}
