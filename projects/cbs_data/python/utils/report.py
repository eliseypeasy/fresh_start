"""
utils/report.py
----------------
Bouwt het volledige HTML-rapport: CSS/typografie (uit parameters.py),
narratieve tekst en de interactieve Plotly-grafieken uit visuals.py.
"""

import datetime as dt

import plotly.io as pio

from utils import parameters as p
from utils import visuals
from utils.data_loader import Datasets


def _fig_html(fig, include_js=False) -> str:
    return pio.to_html(
        fig, include_plotlyjs="cdn" if include_js else False,
        full_html=False, config={"displayModeBar": False, "responsive": True},
    )


CSS = f"""
:root {{
  --ink: {p.INK};
  --paper: {p.PAPER};
  --paper-raised: {p.PAPER_RAISED};
  --grid: {p.GRID};
  --gold: {p.GOLD};
  --teal: {p.TEAL};
  --wine: {p.WINE};
  --muted: {p.MUTED};
  --serif: {p.FONT_SERIF};
  --sans: {p.FONT_SANS};
  --content-width: 700px;
}}

* {{ box-sizing: border-box; }}

body {{
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}}

.layout {{
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  max-width: 1180px;
  margin: 0 auto;
}}

.toc {{
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  overflow-y: auto;
  padding: 48px 20px 48px 32px;
  border-right: 1px solid var(--grid);
}}

.toc-label {{
  font-size: 12px;
  letter-spacing: 0.02em;
  color: var(--muted);
  margin-bottom: 14px;
}}

.toc ol {{ list-style: none; margin: 0; padding: 0; counter-reset: chapter; }}
.toc li {{ counter-increment: chapter; margin-bottom: 4px; }}
.toc a {{
  display: flex;
  gap: 10px;
  color: var(--ink);
  text-decoration: none;
  font-size: 13.5px;
  padding: 6px 8px;
  border-radius: 3px;
}}
.toc a::before {{
  content: counter(chapter);
  color: var(--muted);
  font-variant-numeric: tabular-nums;
  width: 14px;
  flex-shrink: 0;
}}
.toc a:hover {{ background: var(--grid); }}

.main {{ padding: 0 32px 96px; min-width: 0; }}

.hero {{
  max-width: var(--content-width);
  padding: 72px 0 40px;
}}
.hero .eyebrow {{
  color: var(--teal);
  font-size: 13.5px;
  margin: 0 0 14px;
}}
.hero h1 {{
  font-family: var(--serif);
  font-size: 42px;
  line-height: 1.15;
  margin: 0 0 18px;
  font-weight: 600;
}}
.hero p.lede {{
  font-size: 18px;
  color: #3A3729;
  max-width: 60ch;
  margin: 0 0 22px;
}}
.hero .meta {{
  font-size: 13px;
  color: var(--muted);
  border-top: 1px solid var(--grid);
  padding-top: 16px;
  max-width: 60ch;
}}

section.chapter {{
  max-width: var(--content-width);
  padding: 48px 0;
  border-top: 1px solid var(--grid);
}}
section.chapter:first-of-type {{ border-top: none; }}

section.chapter h2 {{
  font-family: var(--serif);
  font-size: 26px;
  font-weight: 600;
  margin: 0 0 18px;
}}
section.chapter h3 {{
  font-family: var(--sans);
  font-size: 15px;
  font-weight: 600;
  color: var(--teal);
  margin: 32px 0 4px;
}}
section.chapter p {{ margin: 0 0 16px; font-size: 15.5px; }}
section.chapter .caption {{
  font-size: 12.5px;
  color: var(--muted);
  margin-top: 8px;
}}

.stat-row {{
  display: flex;
  gap: 28px;
  flex-wrap: wrap;
  margin: 8px 0 28px;
}}
.stat {{
  background: var(--paper-raised);
  border: 1px solid var(--grid);
  border-radius: 4px;
  padding: 14px 18px;
  min-width: 150px;
}}
.stat .num {{
  font-family: var(--serif);
  font-size: 26px;
  display: block;
  line-height: 1.1;
}}
.stat .label {{ font-size: 12px; color: var(--muted); }}

.chart-frame {{
  background: var(--paper-raised);
  border: 1px solid var(--grid);
  border-radius: 4px;
  padding: 18px 18px 6px;
  margin: 20px 0 8px;
  overflow-x: auto;
}}

.callout {{
  border-left: 3px solid var(--gold);
  background: rgba(184, 134, 43, 0.07);
  padding: 14px 18px;
  font-size: 14.5px;
  margin: 20px 0;
}}
.callout strong {{ color: var(--gold); }}

.callout.own {{
  border-left-color: var(--wine);
  background: rgba(140, 59, 74, 0.06);
}}
.callout.own strong {{ color: var(--wine); }}

footer {{
  max-width: var(--content-width);
  padding: 48px 0 96px;
  border-top: 1px solid var(--grid);
  font-size: 13px;
  color: var(--muted);
}}
footer a {{ color: var(--teal); }}

@media (max-width: 860px) {{
  .layout {{ grid-template-columns: 1fr; }}
  .toc {{ position: static; height: auto; border-right: none; border-bottom: 1px solid var(--grid); }}
  .hero h1 {{ font-size: 32px; }}
}}
"""

HOOFDSTUKKEN = [
    ("inleiding", "Inleiding"),
    ("overledenen", "Aantal overledenen"),
    ("leeftijd", "Leeftijdsopbouw"),
    ("levensverwachting", "Levensverwachting"),
    ("eu", "Nederland in Europa"),
    ("gestandaardiseerd", "Gestandaardiseerde sterfte"),
    ("scenario", "Scenario: zonder de pandemie"),
    ("methode", "Methode en bronnen"),
]


def build_report(datasets: Datasets, results: dict) -> str:
    """Bouw het volledige HTML-rapport.

    Parameters
    ----------
    datasets: output van utils.data_loader.load_all()
    results:  output van utils.analysis.run_all(datasets)
    """
    cijfers = results["kerncijfers"]
    aandelen = results["leeftijdsaandelen"]
    eu = results["eu_ranking"]
    scenario = results["scenario_sterfte"]

    fig1 = visuals.fig_sterfte_drieluik(datasets.sterftetrends)
    fig2 = visuals.fig_leeftijdsopbouw(aandelen)
    fig3 = visuals.fig_levensverwachting(datasets.levensverwachting)
    fig4 = visuals.fig_eu_vergelijking(eu)
    fig5 = visuals.fig_gebeurtenissen_annotatie(datasets.sterftetrends, datasets.gebeurtenissen)
    fig6 = visuals.fig_scenario(scenario)

    toc_html = "\n".join(
        f'<li><a href="#{anchor}">{titel}</a></li>' for anchor, titel in HOOFDSTUKKEN
    )

    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trends in sterfte en levensverwachting, Nederland 1950-2024 (eigen analyse)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="{p.GOOGLE_FONTS_URL}" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="layout">

  <nav class="toc">
    <div class="toc-label">Inhoud</div>
    <ol>{toc_html}</ol>
  </nav>

  <main class="main">

    <div class="hero">
      <p class="eyebrow">Eigen analyse &middot; op basis van CBS-open data</p>
      <h1>Trends in sterfte en levensverwachting, Nederland 1950&ndash;2024</h1>
      <p class="lede">
        Een verkenning van hoe lang mensen in Nederland leven, hoeveel mensen
        er jaarlijks overlijden, en wat de coronapandemie daarin structureel
        heeft veranderd &mdash; inclusief een eigen scenario voor wat de
        sterfte had kunnen zijn zonder de pandemie.
      </p>
      <p class="meta">
        Gepubliceerd {dt.date.today().strftime('%-d %B %Y')} &middot; cijfers: CBS &middot;
        dit is een oefenanalyse ter voorbereiding van een sollicitatie, geen
        officiele CBS-publicatie.
      </p>
    </div>

    <section class="chapter" id="inleiding">
      <h2>Inleiding</h2>
      <p>
        In {cijfers['laatste_jaar']} overleden er in Nederland
        {cijfers['overledenen_laatste']:.0f} duizend mensen, ongeveer
        {cijfers['overledenen_verschil']*1000:.0f} meer dan een jaar eerder.
        Dat aantal stijgt al decennia, vooral doordat de bevolking groeit en
        vergrijst. Om te zien of Nederlanders ook echt "meer" of "minder"
        sterven, moet je corrigeren voor die groei en vergrijzing &mdash; dat
        heet standaardiseren, en het is de rode draad van dit rapport.
      </p>
      <p>
        Dit rapport gebruikt cijfers zoals gepubliceerd door het CBS. De
        analyse en de duiding zijn van mij; aan het eind van het rapport
        (hoofdstuk "Scenario") voeg ik een eigen tegenfeitelijke analyse toe
        die niet van het CBS afkomstig is.
      </p>
      <div class="stat-row">
        <div class="stat"><span class="num">{cijfers['lv_mannen_laatste']:.1f} jr</span><span class="label">levensverwachting mannen, {cijfers['laatste_jaar']}</span></div>
        <div class="stat"><span class="num">{cijfers['lv_vrouwen_laatste']:.1f} jr</span><span class="label">levensverwachting vrouwen, {cijfers['laatste_jaar']}</span></div>
        <div class="stat"><span class="num">{cijfers['overledenen_laatste']:.0f}k</span><span class="label">overledenen in {cijfers['laatste_jaar']}</span></div>
      </div>
    </section>

    <section class="chapter" id="overledenen">
      <h2>Aantal overledenen</h2>
      <p>
        Het absolute aantal overledenen zegt op zichzelf weinig: een grotere,
        oudere bevolking levert vanzelf meer sterfgevallen op. Zet je het
        aantal af tegen de bevolkingsomvang (relatief), dan is de stijging
        al veel vlakker. Corrigeer je ook voor de veranderende leeftijdsopbouw
        (gestandaardiseerd), dan zie je een dalende trend &mdash; ondanks de
        stijgende absolute cijfers. Gebruik de knoppen boven de grafiek om
        tussen de drie weergaven te wisselen.
      </p>
      <div class="chart-frame">{_fig_html(fig1, include_js=True)}</div>
      <p class="caption">Bron: CBS, Trends in sterfte en doodsoorzaken 2014&ndash;2024, tabel 3.5.</p>
    </section>

    <section class="chapter" id="leeftijd">
      <h2>Leeftijdsopbouw van de overledenen</h2>
      <p>
        Van alle mensen die in {cijfers['laatste_jaar']} overleden was het
        overgrote deel 80 jaar of ouder. Dat aandeel is de afgelopen dertig
        jaar gestaag gegroeid, terwijl het aandeel overledenen onder de 65
        juist is gekrompen &mdash; een direct gevolg van de vergrijzing en van
        betere overlevingskansen op middelbare leeftijd.
      </p>
      <div class="chart-frame">{_fig_html(fig2)}</div>
      <p class="caption">Bron: CBS, tabel 3.2. Aandelen berekend als percentage van het totaal aantal overledenen per jaar.</p>
    </section>

    <section class="chapter" id="levensverwachting">
      <h2>Levensverwachting</h2>
      <p>
        De levensverwachting bij geboorte laat zien hoe lang iemand
        gemiddeld zou leven als de sterftekansen van dit jaar de rest van
        zijn of haar leven zouden gelden. Voor mannen is dat cijfer in
        {cijfers['laatste_jaar']} inmiddels iets hoger dan vlak voor de
        pandemie ({cijfers['lv_mannen_2019']:.2f} jaar in 2019); voor vrouwen
        ligt het nog altijd iets lager dan in 2019
        ({cijfers['lv_vrouwen_2019']:.2f} jaar).
      </p>
      <div class="chart-frame">{_fig_html(fig3)}</div>
      <p class="caption">Bron: CBS, tabel 3.3.</p>
    </section>

    <section class="chapter" id="eu">
      <h2>Nederland in Europa</h2>
      <p>
        Met een levensverwachting van 82,0 jaar in 2023 zit Nederland boven
        het EU-gemiddelde van 81,5 jaar, maar duidelijk achter koplopers als
        Spanje en Italie. De spreiding tussen EU-landen is groot: bijna tien
        jaar verschil tussen de hoogste en de laagste waarde, wat vooral
        samenhangt met verschillen in welvaart en toegang tot zorg.
      </p>
      <div class="chart-frame">{_fig_html(fig4)}</div>
      <p class="caption">Bron: CBS/Eurostat, tabel 3.4.</p>
    </section>

    <section class="chapter" id="gestandaardiseerd">
      <h2>Gestandaardiseerde sterfte: het langetermijnbeeld</h2>
      <p>
        Gestandaardiseerd voor leeftijd en geslacht daalt de sterfte in
        Nederland al sinds 1950 vrijwel continu &mdash; van 13,2 per duizend
        in 1950 naar een dieptepunt van 5,7 per duizend in 2019. Sinds de
        pandemie ligt dat cijfer structureel hoger en is het nog niet terug
        op het niveau van 2019.
      </p>
      <div class="chart-frame">{_fig_html(fig5)}</div>
      <p class="caption">Bron: CBS, tabel 3.5. Annotaties (griepepidemieen, coronapandemie) op basis van de duiding in dezelfde CBS-publicatie.</p>
      <div class="callout">
        <strong>Waarom standaardiseren?</strong> Zonder correctie voor
        leeftijd zou een vergrijzende bevolking altijd een stijgende sterfte
        laten zien, ook als niemand "sneller" doodgaat dan voorheen.
        Standaardisatie rekent iedereen af tegen eenzelfde referentiebevolking
        (hier: die van 1990), zodat je puur de verandering in sterftekansen
        overhoudt.
      </div>
    </section>

    <section class="chapter" id="scenario">
      <h2>Scenario: zonder de pandemie</h2>
      <p>
        Dit hoofdstuk is mijn eigen toevoeging aan de CBS-cijfers. Ik heb een
        eenvoudige lineaire trend gefit op de gestandaardiseerde sterfte in
        de tien jaar voor de pandemie (2010&ndash;2019) en die trend
        doorgetrokken naar 2020&ndash;{cijfers['laatste_jaar']}. Dat geeft een
        ruwe schatting van waar de sterfte had kunnen liggen als de
        trendbreuk van de pandemie niet had plaatsgevonden.
      </p>
      <div class="chart-frame">{_fig_html(fig6)}</div>
      <p class="caption">Eigen berekening: lineaire trend gefit op CBS-cijfers 2010&ndash;2019, doorgetrokken naar 2020&ndash;{cijfers['laatste_jaar']}.</p>
      <div class="callout own">
        <strong>Wat dit wel en niet zegt.</strong>
        In {cijfers['scenario_jaar']} ligt de gestandaardiseerde sterfte
        ({cijfers['scenario_werkelijk']:.1f} per duizend) nog altijd
        {cijfers['scenario_verschil']:.2f} punt boven wat de trend van voor de
        pandemie zou voorspellen ({cijfers['scenario_verwacht']:.1f} per
        duizend). Ik heb dit bewust niet omgerekend naar een aantal
        "extra" sterfgevallen: daarvoor is een expliciete
        bevolkingsweging per jaar nodig, en die haal ik liever rechtstreeks
        uit StatLine dan dat ik hem zelf benader. Een lineaire extrapolatie
        over vijf jaar is bovendien een grove aanname &mdash; met name
        gedragsveranderingen (zorggebruik, vaccinatiegraad, leefstijl) kunnen
        de werkelijke trend laten afwijken van een simpele rechte lijn. Het
        scenario is dus vooral bedoeld om de vraag scherp te stellen, niet om
        een definitief antwoord te geven.
      </div>
    </section>

    <section class="chapter" id="methode">
      <h2>Methode en bronnen</h2>
      <p>
        Databron voor deze run: <strong>{datasets.bron}</strong>. Dit rapport
        kan op twee manieren gevoed worden, met dezelfde uitkomst-vorm: lokale
        CSV's in <code>input/</code> (vast, reproduceerbaar, precies te weten
        welke cijfers gebruikt zijn) of een live call naar de
        <a href="https://opendata.cbs.nl/statline/portal.html?_la=nl&_catalog=CBS&tableId=37979ned" target="_blank" rel="noopener">CBS StatLine
        open-data API</a> (tabel 37979ned). Welke van de twee gebruikt wordt,
        staat in <code>utils/parameters.py</code> (<code>LOCAL = True/False</code>),
        of kan per run overschreven worden met <code>python main.py --remote</code>.
        Mislukt de live call, dan valt het script automatisch terug op de
        lokale CSV's.
      </p>
      <p>
        De cijfers zijn oorspronkelijk overgenomen uit de CBS-longread
        <em>"Trends in sterfte en doodsoorzaken, 2014-2024"</em>, hoofdstuk 3
        (gepubliceerd 19 maart 2025); de live StatLine-koppeling kan iets
        actuelere cijfers tonen dan die longread, omdat CBS voorlopige cijfers
        later definitief maakt. De leeftijdsuitsplitsing en de EU-vergelijking
        komen in beide gevallen uit de lokale CSV, omdat ik daarvoor nog geen
        even goed geverifieerde live-bron heb gekoppeld.
      </p>
      <p>
        De verwerking gebeurt in Python (pandas voor databewerking, NumPy
        voor de trendfit, Plotly voor de interactieve grafieken). De volledige
        code staat in de bijbehorende repository: <code>main.py</code> als
        startpunt, en <code>utils/</code> met de losse stappen
        (<code>data_loader.py</code>, <code>analysis.py</code>,
        <code>visuals.py</code>, <code>report.py</code>, <code>parameters.py</code>).
      </p>
      <h3>Beperkingen</h3>
      <p>
        Dit is een oefenproject, geen collegiaal getoetste CBS-publicatie.
        De scenario-analyse in het vorige hoofdstuk is met opzet eenvoudig
        gehouden (lineaire trend, geen rekening met leeftijdsstructuurveranderingen
        binnen het scenario zelf) en moet gelezen worden als illustratie van
        een aanpak, niet als een gevalideerde uitkomst.
      </p>
    </section>

    <footer>
      <p>
        Gemaakt als voorbereiding op een sollicitatie. Cijfers: &copy; CBS,
        overgenomen uit de longread
        <a href="{p.CBS_BRON_URL}" target="_blank" rel="noopener">
          "Trends in sterfte en doodsoorzaken, 2014-2024"</a> (CBS, 19 maart 2025).
        Analyse, tekst en vormgeving van dit rapport zijn eigen werk en niet
        gelieerd aan of goedgekeurd door het CBS.
      </p>
    </footer>

  </main>
</div>
</body>
</html>
"""
    return html
