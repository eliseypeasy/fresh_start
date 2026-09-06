# utils/parameters.R
# --------------------------------------------------------------
# Centrale configuratie voor het hele project: paden, analyse-instellingen
# en ontwerp-tokens (kleur/typografie). Zelfde rol als utils/parameters.py
# in de Python-versie van dit project.
#
# Let op: de paden hieronder zijn relatief (input/, output/). Dit script
# gaat er dus van uit dat je het runt vanuit de map r/ zelf (net als bij
# de Python-versie) -- niet vanuit de repo-root of vanuit utils/.

# --- Data: lokaal of live? ---------------------------------------------
LOCAL <- TRUE

# StatLine-tabel "Overledenen; kerncijfers" (CBS, publiek, CC-BY 4.0).
STATLINE_TABLE_ID <- "37979ned"
STATLINE_BASE_URL <- paste0("https://opendata.cbs.nl/ODataApi/OData/", STATLINE_TABLE_ID)
STATLINE_GESLACHT_TOTAAL  <- "T001038"
STATLINE_GESLACHT_MANNEN  <- "3000"
STATLINE_GESLACHT_VROUWEN <- "4000"

# --- Paden --------------------------------------------------------------
INPUT_DIR  <- "input"
OUTPUT_DIR <- "output"

INPUT_FILES <- list(
  overledenen_totaal   = file.path(INPUT_DIR, "overledenen_totaal.csv"),
  overledenen_leeftijd = file.path(INPUT_DIR, "overledenen_leeftijd.csv"),
  levensverwachting     = file.path(INPUT_DIR, "levensverwachting.csv"),
  levensverwachting_eu  = file.path(INPUT_DIR, "levensverwachting_eu.csv"),
  sterftetrends          = file.path(INPUT_DIR, "sterftetrends.csv"),
  gebeurtenissen          = file.path(INPUT_DIR, "gebeurtenissen.csv")
)

REPORT_OUTPUT_PATH       <- file.path(OUTPUT_DIR, "sterfte_trends_rapport.html")
SCENARIO_CSV_OUTPUT_PATH <- file.path(OUTPUT_DIR, "scenario_gestandaardiseerde_sterfte.csv")

# --- Analyse-instellingen -----------------------------------------------
PREPANDEMIE_START <- 2010
PREPANDEMIE_EIND  <- 2019

# --- Ontwerp-tokens (kleur, typografie) ----------------------------------
# Zelfde waarden als de Python-versie, zodat het rapport er identiek uitziet.
INK          <- "#1F2A44"
PAPER        <- "#FAF8F3"
PAPER_RAISED <- "#FFFFFF"
GRID         <- "#E4E0D6"
GOLD         <- "#B8862B"
TEAL         <- "#3E7C8C"
WINE         <- "#8C3B4A"
MUTED        <- "#6B6759"

FONT_SANS  <- "IBM Plex Sans, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
FONT_SERIF <- "Lora, Georgia, serif"
GOOGLE_FONTS_URL <- paste0(
  "https://fonts.googleapis.com/css2?",
  "family=Lora:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap"
)

CBS_BRON_URL <- paste0(
  "https://www.cbs.nl/nl-nl/longread/statistische-trends/2025/",
  "trends-in-sterfte-en-doodsoorzaken-2014-2024/",
  "3-aantal-overledenen-levensverwachting-en-gestandaardiseerde-sterfte"
)
CBS_BRON_LABEL <- 'CBS, "Trends in sterfte en doodsoorzaken, 2014-2024" (19 maart 2025)'
