"""
utils/data_loader.py
---------------------
Leest de brondata in -- lokaal (input/*.csv) of live vanaf CBS StatLine,
afhankelijk van parameters.LOCAL. Zelfde patroon als `params$local` in een
Rmd: 1 vlag, en de rest van de pipeline (analysis.py, visuals.py, report.py)
merkt niets van welk pad is genomen, omdat load_all() in beide gevallen
dezelfde Datasets-vorm teruggeeft.

Bron: CBS StatLine, tabel 37979ned "Overledenen; kerncijfers" (CC-BY 4.0).
https://opendata.cbs.nl/statline/portal.html?_la=nl&_catalog=CBS&tableId=37979ned

Belangrijk: overledenen_leeftijd.csv en levensverwachting_eu.csv worden
altijd lokaal gelezen. Voor de leeftijdsuitsplitsing en de EU-vergelijking
heb ik nog geen passende, geverifieerde live-bron gekoppeld (zie de
toelichting in de docstring van _load_remote() hieronder) -- beter om dat
duidelijk te laten zien dan een niet-geverifieerde koppeling te doen alsof
hij klopt.
"""

from dataclasses import dataclass

import pandas as pd
import requests

from utils.parameters import (
    INPUT_FILES,
    LOCAL,
    STATLINE_BASE_URL,
    STATLINE_GESLACHT_TOTAAL,
    STATLINE_GESLACHT_MANNEN,
    STATLINE_GESLACHT_VROUWEN,
)


@dataclass
class Datasets:
    overledenen_totaal: pd.DataFrame
    overledenen_leeftijd: pd.DataFrame
    levensverwachting: pd.DataFrame
    levensverwachting_eu: pd.DataFrame
    sterftetrends: pd.DataFrame
    gebeurtenissen: pd.DataFrame
    bron: str  # "lokaal" of "CBS StatLine (live)", puur voor logging/rapport


def load_all(local: bool = LOCAL) -> Datasets:
    """Centraal instappunt. `local` overschrijft parameters.LOCAL indien opgegeven.

    local=True  -> input/*.csv
    local=False -> live ophalen bij CBS StatLine, met automatische terugval
                   naar de lokale CSV's als de live call om wat voor reden
                   dan ook mislukt (geen netwerktoegang, tabel offline, etc.)
    """
    if local:
        return _load_local()

    try:
        return _load_remote()
    except Exception as e:
        print(f"[data_loader] Live ophalen bij CBS StatLine mislukt ({e}).")
        print("[data_loader] Terugvallen op lokale CSV's in input/.")
        return _load_local()


def _load_local() -> Datasets:
    overledenen_totaal = pd.read_csv(INPUT_FILES["overledenen_totaal"])
    overledenen_totaal["voorlopig"] = (
        overledenen_totaal["jaar"] == overledenen_totaal["jaar"].max()
    )

    return Datasets(
        overledenen_totaal=overledenen_totaal,
        overledenen_leeftijd=pd.read_csv(INPUT_FILES["overledenen_leeftijd"]),
        levensverwachting=pd.read_csv(INPUT_FILES["levensverwachting"]),
        levensverwachting_eu=pd.read_csv(INPUT_FILES["levensverwachting_eu"]),
        sterftetrends=pd.read_csv(INPUT_FILES["sterftetrends"]),
        gebeurtenissen=pd.read_csv(INPUT_FILES["gebeurtenissen"]),
        bron="lokaal (input/*.csv)",
    )


def _load_remote() -> Datasets:
    """Haal de cijfers live op bij CBS StatLine (tabel 37979ned).

    Dekt overledenen_totaal, sterftetrends en levensverwachting -- deze drie
    staan namelijk allemaal in dezelfde StatLine-tabel, uitgesplitst naar
    Geslacht en Perioden. overledenen_leeftijd (leeftijdsopbouw) en
    levensverwachting_eu (EU-vergelijking, Eurostat) komen bewust nog uit de
    lokale CSV: ik heb voor die twee geen StatLine/Eurostat-tabel geverifieerd
    op exact dezelfde manier als voor 37979ned, en wil geen ID raden.
    """
    resp = requests.get(f"{STATLINE_BASE_URL}/TypedDataSet", timeout=30)
    resp.raise_for_status()
    raw = pd.DataFrame(resp.json()["value"])

    raw["Geslacht"] = raw["Geslacht"].str.strip()
    raw["jaar"] = raw["Perioden"].str[:4].astype(int)
    # Enkel jaartotalen (Perioden eindigt op "JJ00"); StatLine-tabellen
    # bevatten soms ook kwartaal/maandregels die we hier niet willen.
    raw = raw[raw["Perioden"].str.endswith("JJ00")]

    totaal = raw[raw["Geslacht"] == STATLINE_GESLACHT_TOTAAL].sort_values("jaar")

    overledenen_totaal = pd.DataFrame({
        "jaar": totaal["jaar"],
        "overledenen_x1000": totaal["Overledenen_1"] / 1000,
    })
    overledenen_totaal["voorlopig"] = (
        overledenen_totaal["jaar"] == overledenen_totaal["jaar"].max()
    )

    sterftetrends = pd.DataFrame({
        "jaar": totaal["jaar"],
        "overledenen_x10000": totaal["Overledenen_1"] / 10000,
        "overledenen_relatief": totaal["OverledenenRelatief_2"],
        "overledenen_gestandaardiseerd": totaal["OverledenenGestandaardiseerd_3"],
    })

    mannen = raw[raw["Geslacht"] == STATLINE_GESLACHT_MANNEN].sort_values("jaar")
    vrouwen = raw[raw["Geslacht"] == STATLINE_GESLACHT_VROUWEN].sort_values("jaar")
    levensverwachting = pd.merge(
        mannen[["jaar", "LevensverwachtingBijGeboorte_12"]].rename(
            columns={"LevensverwachtingBijGeboorte_12": "mannen"}),
        vrouwen[["jaar", "LevensverwachtingBijGeboorte_12"]].rename(
            columns={"LevensverwachtingBijGeboorte_12": "vrouwen"}),
        on="jaar",
    )
    # Zelfde venster als de lokale CSV, voor een eerlijke vergelijking tussen
    # local=True en local=False.
    levensverwachting = levensverwachting[levensverwachting["jaar"] >= 1995]

    return Datasets(
        overledenen_totaal=overledenen_totaal.reset_index(drop=True),
        overledenen_leeftijd=pd.read_csv(INPUT_FILES["overledenen_leeftijd"]),
        levensverwachting=levensverwachting.reset_index(drop=True),
        levensverwachting_eu=pd.read_csv(INPUT_FILES["levensverwachting_eu"]),
        sterftetrends=sterftetrends.reset_index(drop=True),
        gebeurtenissen=pd.read_csv(INPUT_FILES["gebeurtenissen"]),
        bron="CBS StatLine (live, tabel 37979ned)",
    )
