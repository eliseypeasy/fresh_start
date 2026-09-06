"""
utils/parameters.py
--------------------
Centrale configuratie voor het hele project: paden, analyse-instellingen en
ontwerp-tokens (kleur/typografie). Als je iets wilt aanpassen -- een kleur,
het trendvenster voor het scenario, waar bestanden heen geschreven worden --
is dit de plek.
"""

from pathlib import Path

# --- Bron van de data ----------------------------------------------------
# True  -> lees de CSV's in input/ (snel, reproduceerbaar, "bevroren" op het
#          moment dat de CSV's zijn weggeschreven -- prettig voor onderzoek
#          waar je precies wil weten welke cijfers je gebruikt hebt).
# False -> haal de cijfers live op bij CBS StatLine (OData API, tabel
#          37979ned). Kan afwijken van de lokale CSV's als CBS de cijfers
#          heeft herzien (bijv. voorlopig -> definitief).
# Zelfde patroon als params$local in een Rmd: 1 vlag, gebruikt door
# data_loader.load_all() om te kiezen welk pad te nemen.
LOCAL = True

# StatLine-tabel "Overledenen; kerncijfers" (CBS, publiek, CC-BY 4.0).
# Bevat: Overledenen_1, OverledenenRelatief_2, OverledenenGestandaardiseerd_3,
# LevensverwachtingBijGeboorte_12, uitgesplitst naar Geslacht en Perioden.
# Dekt bij remote fetch: overledenen_totaal, sterftetrends, levensverwachting.
# https://opendata.cbs.nl/statline/portal.html?_la=nl&_catalog=CBS&tableId=37979ned
STATLINE_TABLE_ID = "37979ned"
STATLINE_BASE_URL = f"https://opendata.cbs.nl/ODataApi/OData/{STATLINE_TABLE_ID}"
STATLINE_GESLACHT_TOTAAL = "T001038"
STATLINE_GESLACHT_MANNEN = "3000"
STATLINE_GESLACHT_VROUWEN = "4000"

# --- Paden ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT_DIR / "input"
OUTPUT_DIR = ROOT_DIR / "output"

INPUT_FILES = {
    "overledenen_totaal": INPUT_DIR / "overledenen_totaal.csv",
    "overledenen_leeftijd": INPUT_DIR / "overledenen_leeftijd.csv",
    "levensverwachting": INPUT_DIR / "levensverwachting.csv",
    "levensverwachting_eu": INPUT_DIR / "levensverwachting_eu.csv",
    "sterftetrends": INPUT_DIR / "sterftetrends.csv",
    "gebeurtenissen": INPUT_DIR / "gebeurtenissen.csv",
}

REPORT_OUTPUT_PATH = OUTPUT_DIR / "sterfte_trends_rapport.html"
SCENARIO_CSV_OUTPUT_PATH = OUTPUT_DIR / "scenario_gestandaardiseerde_sterfte.csv"

# --- Analyse-instellingen ----------------------------------------------
# Venster gebruikt om de "pre-corona trend" op te fitten voor het scenario
# in hoofdstuk 7 van het rapport.
PREPANDEMIE_START = 2010
PREPANDEMIE_EIND = 2019

# --- Ontwerp-tokens (kleur, typografie) ---------------------------------
# Gebruikt door utils/visuals.py en utils/report.py, zodat de hele
# huisstijl van het rapport op een plek staat.
INK = "#1F2A44"          # primaire lijnkleur / tekst
PAPER = "#FAF8F3"        # paginakleur (warm off-white)
PAPER_RAISED = "#FFFFFF"
GRID = "#E4E0D6"
GOLD = "#B8862B"         # accent: annotaties / scenario
TEAL = "#3E7C8C"         # secundaire reeks
WINE = "#8C3B4A"         # tertiaire reeks
MUTED = "#6B6759"

FONT_SANS = "IBM Plex Sans, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
FONT_SERIF = "Lora, Georgia, serif"
GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Lora:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap"
)

CBS_BRON_URL = (
    "https://www.cbs.nl/nl-nl/longread/statistische-trends/2025/"
    "trends-in-sterfte-en-doodsoorzaken-2014-2024/"
    "3-aantal-overledenen-levensverwachting-en-gestandaardiseerde-sterfte"
)
CBS_BRON_LABEL = 'CBS, "Trends in sterfte en doodsoorzaken, 2014-2024" (19 maart 2025)'
