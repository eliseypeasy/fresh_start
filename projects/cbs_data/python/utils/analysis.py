"""
utils/analysis.py
------------------
Berekeningen op de ingelezen CBS-cijfers.

Twee soorten analyse:
1. Reproductie van de CBS-standaardmethode (gestandaardiseerde sterfte,
   levensverwachting, leeftijdsaandelen) -- bewust dezelfde aanpak die het
   CBS zelf hanteert. Bij een officiele statistiek is consistente,
   uniforme methodologie een vereiste, geen plek voor "creativiteit".
2. Een eigen toevoeging: een tegenfeitelijk (counterfactual) scenario
   "wat als de trend van voor de pandemie was doorgezet?", op basis van
   een eenvoudige lineaire extrapolatie (zie parameters.PREPANDEMIE_*).
   Dit is nadrukkelijk eigen werk, geen CBS-cijfer.
"""

import numpy as np
import pandas as pd

from utils.data_loader import Datasets
from utils.parameters import PREPANDEMIE_START, PREPANDEMIE_EIND


def fit_trend(df: pd.DataFrame, jaar_col: str, waarde_col: str,
              start: int, eind: int) -> tuple[float, float]:
    """Fit een simpele lineaire trend (jaar -> waarde) op het venster [start, eind]."""
    subset = df[(df[jaar_col] >= start) & (df[jaar_col] <= eind)]
    helling, intercept = np.polyfit(subset[jaar_col], subset[waarde_col], deg=1)
    return helling, intercept


def counterfactual_gestandaardiseerde_sterfte(sterftetrends: pd.DataFrame) -> pd.DataFrame:
    """Eigen scenario: extrapoleer de pre-pandemie trend en vergelijk met werkelijk."""
    helling, intercept = fit_trend(
        sterftetrends, "jaar", "overledenen_gestandaardiseerd",
        PREPANDEMIE_START, PREPANDEMIE_EIND,
    )
    scenario = sterftetrends[["jaar", "overledenen_gestandaardiseerd"]].copy()
    scenario = scenario.rename(columns={"overledenen_gestandaardiseerd": "werkelijk"})
    scenario["verwacht_pre_corona_trend"] = intercept + helling * scenario["jaar"]
    scenario["verschil"] = scenario["werkelijk"] - scenario["verwacht_pre_corona_trend"]
    return scenario


def counterfactual_levensverwachting(levensverwachting: pd.DataFrame) -> pd.DataFrame:
    """Zelfde eigen scenario, maar dan voor levensverwachting (mannen/vrouwen)."""
    out = levensverwachting[["jaar", "mannen", "vrouwen"]].copy()
    for geslacht in ["mannen", "vrouwen"]:
        helling, intercept = fit_trend(
            levensverwachting, "jaar", geslacht, PREPANDEMIE_START, PREPANDEMIE_EIND,
        )
        out[f"{geslacht}_verwacht"] = intercept + helling * out["jaar"]
        out[f"{geslacht}_verschil"] = out[geslacht] - out[f"{geslacht}_verwacht"]
    return out


def leeftijdsaandelen(overledenen_leeftijd: pd.DataFrame) -> pd.DataFrame:
    """Aandeel overledenen per leeftijdsgroep, per jaar (voor het stapeldiagram)."""
    df = overledenen_leeftijd.copy()
    df["totaal"] = df["leeftijd_0_65"] + df["leeftijd_65_80"] + df["leeftijd_80_plus"]
    for col in ["leeftijd_0_65", "leeftijd_65_80", "leeftijd_80_plus"]:
        df[f"{col}_aandeel"] = df[col] / df["totaal"]
    return df


def eu_ranking(levensverwachting_eu: pd.DataFrame) -> pd.DataFrame:
    """Sorteer EU-landen op levensverwachting 2023, met NL-markering."""
    df = levensverwachting_eu.sort_values("jaar_2023", ascending=True).reset_index(drop=True)
    df["is_nl"] = df["land"] == "Nederland"
    return df


def kerncijfers(datasets: Datasets, scenario: pd.DataFrame) -> dict:
    """Een klein aantal samenvattende kerncijfers voor de inleiding van het rapport."""
    laatste = datasets.overledenen_totaal.iloc[-1]
    vorige = datasets.overledenen_totaal.iloc[-2]
    lv = datasets.levensverwachting
    lv_laatste = lv.iloc[-1]
    lv_2019 = lv[lv["jaar"] == 2019].iloc[0]
    laatste_scenario = scenario.iloc[-1]

    return {
        "laatste_jaar": int(laatste["jaar"]),
        "overledenen_laatste": laatste["overledenen_x1000"],
        "overledenen_verschil": laatste["overledenen_x1000"] - vorige["overledenen_x1000"],
        "lv_mannen_laatste": lv_laatste["mannen"],
        "lv_vrouwen_laatste": lv_laatste["vrouwen"],
        "lv_mannen_2019": lv_2019["mannen"],
        "lv_vrouwen_2019": lv_2019["vrouwen"],
        "scenario_jaar": int(laatste_scenario["jaar"]),
        "scenario_werkelijk": laatste_scenario["werkelijk"],
        "scenario_verwacht": laatste_scenario["verwacht_pre_corona_trend"],
        "scenario_verschil": laatste_scenario["verschil"],
    }


def run_all(datasets: Datasets) -> dict:
    """Voer alle analyses in een keer uit en geef alles terug als 1 dict.

    Dit is de functie die main.py aanroept, zodat main.py zelf niet elke
    losse analysefunctie hoeft te kennen.
    """
    scenario_sterfte = counterfactual_gestandaardiseerde_sterfte(datasets.sterftetrends)
    scenario_lv = counterfactual_levensverwachting(datasets.levensverwachting)
    aandelen = leeftijdsaandelen(datasets.overledenen_leeftijd)
    eu = eu_ranking(datasets.levensverwachting_eu)
    cijfers = kerncijfers(datasets, scenario_sterfte)

    return {
        "scenario_sterfte": scenario_sterfte,
        "scenario_levensverwachting": scenario_lv,
        "leeftijdsaandelen": aandelen,
        "eu_ranking": eu,
        "kerncijfers": cijfers,
    }
