# Trends in sterfte en levensverwachting, NL 1950–2024 (R-versie)

R-versie van hetzelfde project als de map `python/` ernaast: een
interactief HTML-rapport over sterfte, levensverwachting en
gestandaardiseerde sterfte in Nederland, met precies dezelfde output,
dezelfde databronnen (lokaal of live CBS StatLine) en dezelfde
projectstructuur — nu in R in plaats van Python.

## Waarom een los R-script en geen R Markdown?

De HTML/CSS-layout in `utils/report.R` is met opzet custom gebouwd (sticky
zijbalk, eigen typografie, eigen kleurenschema). Een Rmd/knitr-document
voegt daar zijn eigen HTML-wrapper, CSS en Bootstrap-afhankelijkheden aan
toe, wat met deze layout zou botsen. Een kaal R-script met een eigen
HTML-sjabloon geeft volledige controle over de output — vergelijkbaar met
hoe de Python-versie `plotly.io.to_html(..., full_html=False)` gebruikt om
alleen een grafiek-fragment te krijgen in plaats van een hele pagina.

## Projectstructuur (zelfde als python/)

```
r/
├── main.R                geen functie eromheen, "# %%"-cellen per stap
├── requirements.R         installeert jsonlite + httr
├── input/                 brondata (CBS, als CSV) -- zelfde bestanden als python/input/
├── utils/
│   ├── parameters.R       configuratie: paden, kleuren/fonts, StatLine-tabel-ID
│   ├── data_loader.R      leest input/*.csv IN of haalt live op bij CBS StatLine
│   ├── analysis.R         standaardmethode (o.a. lm() voor de trendfit) + eigen scenario
│   ├── visuals.R           bouwt Plotly data/layout-specs als kale R-lists
│   └── report.R            HTML/CSS-sjabloon + fig_to_html() (JSON via jsonlite)
└── output/                 sterfte_trends_rapport.html + scenario-tabel (csv)
```

## Verschil met de Python-versie: geen `plotly`-package nodig

De Python-versie gebruikt `plotly.graph_objects` om figuren te bouwen en
`pio.to_html()` om ze te serialiseren. In R zou het R-package `plotly` dat
ook kunnen (het is een wrapper om exact dezelfde plotly.js), maar het trekt
best veel dependencies mee (`htmlwidgets`, `crosstalk`, ...) voor iets wat
uiteindelijk toch alleen JSON hoeft te worden. `utils/visuals.R` bouwt daarom
gewone R-lists die 1-op-1 dezelfde vorm hebben als de Plotly JSON-structuur;
`utils/report.R::fig_to_html()` zet zo'n list om in een `<div>` +
`<script>Plotly.newPlot(...)</script>`-fragment met `jsonlite::toJSON()`,
en laadt Plotly.js zelf 1x via het CDN. Alleen `jsonlite` en `httr` zijn dus
nodig als externe packages.

## Gebruik

```bash
Rscript requirements.R   # eenmalig, installeert jsonlite + httr
Rscript main.R
```

Of in Positron/RStudio: open `main.R`, run cel voor cel (de "# %%"-regels)
of het hele script in 1 keer met Source. Zorg dat de working directory de
map `r/` is (niet de repo-root), anders kloppen de relatieve paden in
`utils/parameters.R` niet.

Om de live CBS StatLine-koppeling te gebruiken in plaats van de lokale
CSV's: verander bovenaan in `main.R` de regel `local <- TRUE` naar
`local <- FALSE`. Zie de `python/`-README voor meer over waarom deze twee
opties er zijn en welke tabel (37979ned) er gebruikt wordt.

## Output

- `output/sterfte_trends_rapport.html` — het interactieve rapport, identiek
  aan de Python-versie qua lay-out, tekst en cijfers.
- `output/scenario_gestandaardiseerde_sterfte.csv` — de onderliggende
  cijfers van het eigen scenario (werkelijk vs. verwacht bij doortrekken
  van de pre-corona trend).

## Beperkingen

Zelfde als de Python-versie: dit is een oefenproject, geen collegiaal
getoetste publicatie. De live StatLine-koppeling dekt alleen
`overledenen_totaal`, `sterftetrends` en `levensverwachting` (tabel
37979ned); de leeftijdsuitsplitsing en de EU-vergelijking komen altijd uit
de lokale CSV.
