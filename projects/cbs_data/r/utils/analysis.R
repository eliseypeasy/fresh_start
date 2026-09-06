# utils/analysis.R
# --------------------------------------------------------------
# Berekeningen op de ingelezen CBS-cijfers.
#
# Twee soorten analyse:
# 1. Reproductie van de CBS-standaardmethode (gestandaardiseerde sterfte,
#    levensverwachting, leeftijdsaandelen) -- bewust dezelfde aanpak die
#    het CBS zelf hanteert.
# 2. Een eigen toevoeging: een tegenfeitelijk (counterfactual) scenario
#    "wat als de trend van voor de pandemie was doorgezet?", op basis van
#    een simpele lineaire regressie (lm()) -- zie PREPANDEMIE_* in
#    parameters.R. Dit is nadrukkelijk eigen werk, geen CBS-cijfer.

# Fit een lineaire trend (jaar -> waarde) op het venster [start, eind].
# Geeft helling en intercept terug (zelfde interface als de Python-versie,
# die numpy.polyfit gebruikt; hier is lm() het R-equivalent).
fit_trend <- function(df, jaar_col, waarde_col, start, eind) {
  subset_df <- df[df[[jaar_col]] >= start & df[[jaar_col]] <= eind, ]
  fit <- lm(subset_df[[waarde_col]] ~ subset_df[[jaar_col]])
  list(helling = unname(coef(fit)[2]), intercept = unname(coef(fit)[1]))
}

counterfactual_gestandaardiseerde_sterfte <- function(sterftetrends) {
  trend <- fit_trend(sterftetrends, "jaar", "overledenen_gestandaardiseerd",
                      PREPANDEMIE_START, PREPANDEMIE_EIND)

  scenario <- data.frame(
    jaar = sterftetrends$jaar,
    werkelijk = sterftetrends$overledenen_gestandaardiseerd
  )
  scenario$verwacht_pre_corona_trend <- trend$intercept + trend$helling * scenario$jaar
  scenario$verschil <- scenario$werkelijk - scenario$verwacht_pre_corona_trend
  scenario
}

counterfactual_levensverwachting <- function(levensverwachting) {
  out <- levensverwachting[, c("jaar", "mannen", "vrouwen")]
  for (geslacht in c("mannen", "vrouwen")) {
    trend <- fit_trend(levensverwachting, "jaar", geslacht, PREPANDEMIE_START, PREPANDEMIE_EIND)
    out[[paste0(geslacht, "_verwacht")]] <- trend$intercept + trend$helling * out$jaar
    out[[paste0(geslacht, "_verschil")]] <- out[[geslacht]] - out[[paste0(geslacht, "_verwacht")]]
  }
  out
}

# Aandeel overledenen per leeftijdsgroep, per jaar (voor het stapeldiagram).
leeftijdsaandelen <- function(overledenen_leeftijd) {
  df <- overledenen_leeftijd
  df$totaal <- df$leeftijd_0_65 + df$leeftijd_65_80 + df$leeftijd_80_plus
  for (col in c("leeftijd_0_65", "leeftijd_65_80", "leeftijd_80_plus")) {
    df[[paste0(col, "_aandeel")]] <- df[[col]] / df$totaal
  }
  df
}

# Sorteer EU-landen op levensverwachting 2023, met NL-markering.
eu_ranking <- function(levensverwachting_eu) {
  df <- levensverwachting_eu[order(levensverwachting_eu$jaar_2023), ]
  df$is_nl <- df$land == "Nederland"
  rownames(df) <- NULL
  df
}

# Een klein aantal samenvattende kerncijfers voor de inleiding van het rapport.
kerncijfers <- function(datasets, scenario) {
  n <- nrow(datasets$overledenen_totaal)
  laatste <- datasets$overledenen_totaal[n, ]
  vorige  <- datasets$overledenen_totaal[n - 1, ]

  lv <- datasets$levensverwachting
  lv_laatste <- lv[nrow(lv), ]
  lv_2019 <- lv[lv$jaar == 2019, ]

  laatste_scenario <- scenario[nrow(scenario), ]

  list(
    laatste_jaar = laatste$jaar,
    overledenen_laatste = laatste$overledenen_x1000,
    overledenen_verschil = laatste$overledenen_x1000 - vorige$overledenen_x1000,
    lv_mannen_laatste = lv_laatste$mannen,
    lv_vrouwen_laatste = lv_laatste$vrouwen,
    lv_mannen_2019 = lv_2019$mannen,
    lv_vrouwen_2019 = lv_2019$vrouwen,
    scenario_jaar = laatste_scenario$jaar,
    scenario_werkelijk = laatste_scenario$werkelijk,
    scenario_verwacht = laatste_scenario$verwacht_pre_corona_trend,
    scenario_verschil = laatste_scenario$verschil
  )
}

# Voer alle analyses in 1 keer uit en geef alles terug als 1 lijst -- dit
# is de functie die main.R aanroept.
run_all <- function(datasets) {
  scenario_sterfte <- counterfactual_gestandaardiseerde_sterfte(datasets$sterftetrends)
  scenario_lv <- counterfactual_levensverwachting(datasets$levensverwachting)
  aandelen <- leeftijdsaandelen(datasets$overledenen_leeftijd)
  eu <- eu_ranking(datasets$levensverwachting_eu)
  cijfers <- kerncijfers(datasets, scenario_sterfte)

  list(
    scenario_sterfte = scenario_sterfte,
    scenario_levensverwachting = scenario_lv,
    leeftijdsaandelen = aandelen,
    eu_ranking = eu,
    kerncijfers = cijfers
  )
}
