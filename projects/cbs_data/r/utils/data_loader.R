# utils/data_loader.R
# --------------------------------------------------------------
# Leest de brondata in -- lokaal (input/*.csv) of live vanaf CBS StatLine,
# afhankelijk van het `local` argument (default: LOCAL uit parameters.R).
# Zelfde toggle als in de Python-versie: load_all() geeft in beide gevallen
# exact dezelfde lijst-vorm terug (zelfde namen, zelfde kolommen), dus de
# rest van de pipeline (analysis.R, visuals.R, report.R) merkt niet welk
# pad genomen is.
#
# Bron: CBS StatLine, tabel 37979ned "Overledenen; kerncijfers" (CC-BY 4.0).
# https://opendata.cbs.nl/statline/portal.html?_la=nl&_catalog=CBS&tableId=37979ned

load_all <- function(local = LOCAL) {
  if (isTRUE(local)) {
    return(load_local())
  }
  result <- tryCatch(load_remote(), error = function(e) {
    message("[data_loader] Live ophalen bij CBS StatLine mislukt (", conditionMessage(e), ").")
    message("[data_loader] Terugvallen op lokale CSV's in input/.")
    NULL
  })
  if (is.null(result)) load_local() else result
}

load_local <- function() {
  overledenen_totaal <- read.csv(INPUT_FILES$overledenen_totaal, stringsAsFactors = FALSE)
  overledenen_totaal$voorlopig <- overledenen_totaal$jaar == max(overledenen_totaal$jaar)

  list(
    overledenen_totaal   = overledenen_totaal,
    overledenen_leeftijd = read.csv(INPUT_FILES$overledenen_leeftijd, stringsAsFactors = FALSE),
    levensverwachting     = read.csv(INPUT_FILES$levensverwachting, stringsAsFactors = FALSE),
    levensverwachting_eu  = read.csv(INPUT_FILES$levensverwachting_eu, stringsAsFactors = FALSE),
    sterftetrends          = read.csv(INPUT_FILES$sterftetrends, stringsAsFactors = FALSE),
    gebeurtenissen          = read.csv(INPUT_FILES$gebeurtenissen, stringsAsFactors = FALSE),
    bron = "lokaal (input/*.csv)"
  )
}

# Haalt de cijfers live op bij CBS StatLine (tabel 37979ned). Dekt
# overledenen_totaal, sterftetrends en levensverwachting; die 3 staan
# namelijk allemaal in dezelfde tabel, uitgesplitst naar Geslacht en
# Perioden. overledenen_leeftijd en levensverwachting_eu komen bewust nog
# uit de lokale CSV (zie README voor waarom).
load_remote <- function() {
  resp <- httr::GET(paste0(STATLINE_BASE_URL, "/TypedDataSet"), httr::timeout(30))
  httr::stop_for_status(resp)
  raw <- jsonlite::fromJSON(httr::content(resp, as = "text", encoding = "UTF-8"))$value

  raw$Geslacht <- trimws(raw$Geslacht)
  raw$jaar <- as.integer(substr(raw$Perioden, 1, 4))
  raw <- raw[endsWith(raw$Perioden, "JJ00"), ]

  totaal <- raw[raw$Geslacht == STATLINE_GESLACHT_TOTAAL, ]
  totaal <- totaal[order(totaal$jaar), ]

  overledenen_totaal <- data.frame(
    jaar = totaal$jaar,
    overledenen_x1000 = totaal$Overledenen_1 / 1000
  )
  overledenen_totaal$voorlopig <- overledenen_totaal$jaar == max(overledenen_totaal$jaar)

  sterftetrends <- data.frame(
    jaar = totaal$jaar,
    overledenen_x10000 = totaal$Overledenen_1 / 10000,
    overledenen_relatief = totaal$OverledenenRelatief_2,
    overledenen_gestandaardiseerd = totaal$OverledenenGestandaardiseerd_3
  )

  mannen  <- raw[raw$Geslacht == STATLINE_GESLACHT_MANNEN, c("jaar", "LevensverwachtingBijGeboorte_12")]
  vrouwen <- raw[raw$Geslacht == STATLINE_GESLACHT_VROUWEN, c("jaar", "LevensverwachtingBijGeboorte_12")]
  names(mannen)[2]  <- "mannen"
  names(vrouwen)[2] <- "vrouwen"
  levensverwachting <- merge(mannen, vrouwen, by = "jaar")
  levensverwachting <- levensverwachting[levensverwachting$jaar >= 1995, ]
  levensverwachting <- levensverwachting[order(levensverwachting$jaar), ]

  list(
    overledenen_totaal   = overledenen_totaal,
    overledenen_leeftijd = read.csv(INPUT_FILES$overledenen_leeftijd, stringsAsFactors = FALSE),
    levensverwachting     = levensverwachting,
    levensverwachting_eu  = read.csv(INPUT_FILES$levensverwachting_eu, stringsAsFactors = FALSE),
    sterftetrends          = sterftetrends,
    gebeurtenissen          = read.csv(INPUT_FILES$gebeurtenissen, stringsAsFactors = FALSE),
    bron = "CBS StatLine (live, tabel 37979ned)"
  )
}
