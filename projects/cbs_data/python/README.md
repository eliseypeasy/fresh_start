# Trends in sterfte en levensverwachting, NL 1950–2024

Een oefenproject: een interactief HTML-rapport over sterfte, levensverwachting
en gestandaardiseerde sterfte in Nederland, gebouwd in Python op basis van
door het CBS gepubliceerde cijfers.

Gemaakt als voorbereiding op sollicitaties bij CBS (onderzoeker
doodsoorzakenstatistiek) en gemeente Leiden (data-analist) — vandaar de keuze
voor dit onderwerp, en de nadruk op zowel gestandaardiseerde statistische
methode als heldere, interactieve visualisatie.

## Wat dit laat zien

- **Standaard CBS-methodologie**: gestandaardiseerde sterfte, levensverwachting
  bij geboorte, leeftijdsopbouw — berekend op dezelfde manier als het CBS dat
  zelf doet, omdat consistentie hier belangrijker is dan originaliteit.
- **Eigen toevoeging**: een tegenfeitelijk scenario ("wat als de trend van
  vóór de pandemie was doorgezet?") op basis van een eenvoudige lineaire
  trendextrapolatie — nadrukkelijk eigen analyse, duidelijk gelabeld als
  zodanig in het rapport.
- **Interactieve visualisatie** met Plotly (hover-tooltips, een knoppen-
  toggle tussen absolute/relatieve/gestandaardiseerde weergave), in een eigen
  vormgeving die qua sfeer aansluit bij een officiële statistische publicatie
  zonder de CBS-huisstijl te kopiëren.

## Data: lokaal óf live (params-stijl toggle)

`utils/parameters.py` heeft een `LOCAL` vlag, hetzelfde idee als
`params$local` in een Rmd:

```python
LOCAL = True   # input/*.csv -- vast, reproduceerbaar, precies te weten
               # welke cijfers gebruikt zijn op het moment van schrijven
LOCAL = False  # live via de CBS StatLine open-data API (tabel 37979ned)
               # -- kan afwijken van de lokale CSV's als CBS voorlopige
               # cijfers inmiddels definitief heeft gemaakt
```

Overschrijven per run kan ook zonder `parameters.py` aan te passen:

```bash
python main.py             # gebruikt parameters.LOCAL
python main.py --remote    # forceert live StatLine-call
python main.py --local     # forceert lokale CSV's
```

Bij `--remote` haalt `utils/data_loader.py` de cijfers rechtstreeks op bij
[CBS StatLine, tabel 37979ned "Overledenen; kerncijfers"](https://opendata.cbs.nl/statline/portal.html?_la=nl&_catalog=CBS&tableId=37979ned)
(CC-BY 4.0) — dezelfde tabel dekt `overledenen_totaal`, `sterftetrends` én
`levensverwachting`. Mislukt die live call (geen netwerktoegang, tabel
tijdelijk offline), dan valt het script automatisch terug op de lokale CSV's
en meldt dat expliciet in de console-output.

`overledenen_leeftijd` (leeftijdsopbouw) en `levensverwachting_eu`
(EU-vergelijking, Eurostat) komen in beide gevallen uit de lokale CSV: ik heb
daar geen StatLine/Eurostat-tabel voor geverifieerd op dezelfde manier als
voor 37979ned, en wilde geen tabel-ID raden.

Oorspronkelijke bron van de lokale CSV's:
> CBS (2025). *Trends in sterfte en doodsoorzaken, 2014-2024*, hoofdstuk 3.
> https://www.cbs.nl/nl-nl/longread/statistische-trends/2025/trends-in-sterfte-en-doodsoorzaken-2014-2024/3-aantal-overledenen-levensverwachting-en-gestandaardiseerde-sterfte

## Projectstructuur

```
cbs_data/
├── main.py              startpunt: leest, analyseert, bouwt het rapport
├── requirements.txt
├── input/                brondata (CBS, als CSV)
│   ├── overledenen_totaal.csv
│   ├── overledenen_leeftijd.csv
│   ├── levensverwachting.csv
│   ├── levensverwachting_eu.csv
│   ├── sterftetrends.csv
│   └── gebeurtenissen.csv
├── utils/
│   ├── parameters.py     configuratie: LOCAL-vlag, StatLine-tabel-ID, paden, kleuren/fonts
│   ├── data_loader.py    leest input/*.csv IN of haalt live op bij CBS StatLine
│   ├── analysis.py       standaardmethode + eigen scenario-berekening
│   ├── visuals.py        Plotly-figuren
│   └── report.py         HTML/CSS-assemblage + narratieve tekst
└── output/                weggeschreven resultaten
    ├── sterfte_trends_rapport.html
    └── scenario_gestandaardiseerde_sterfte.csv
```

`main.py` is het enige bestand dat je hoeft te lezen om te snappen hoe alles
samenkomt — het roept in volgorde `data_loader`, `analysis`, en `report` aan
en schrijft de output weg. Elke `utils`-module doet precies één ding en is
op zichzelf te lezen zonder de rest van het project te kennen.

## Gebruik

```bash
pip install -r requirements.txt
python main.py
```

Dit schrijft twee bestanden naar `output/`:
- `sterfte_trends_rapport.html` — het interactieve rapport. Zelfstandig
  bestand (Plotly wordt via CDN geladen), te openen in elke browser of te
  hosten zonder build-stap.
- `scenario_gestandaardiseerde_sterfte.csv` — de onderliggende cijfers van
  het eigen scenario (werkelijk vs. verwacht bij doortrekken van de
  pre-corona trend), als voorbeeld van een concrete csv-tabel-output.

## Beperkingen

Dit is een oefenproject, geen collegiaal getoetste publicatie. Het scenario
in het rapport gebruikt bewust een eenvoudige lineaire trend en rekent het
verschil niet om naar een aantal sterfgevallen, om geen ongefundeerde
aannames over bevolkingsomvang te hoeven doen.
