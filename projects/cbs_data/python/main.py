"""
main.py
-------
Startpunt van het project. 
1. Data inlezen
2. Analyse: standaardmethode + eigen scenario
3. Rapport bouwen (grafieken + HTML) 
4. Wegschrijven naar output/ 

Zie output map voor HTML-rapport
"""

from utils import analysis, data_loader, parameters as p, report

# %% Instelling: lokale CSV's of live CBS StatLine? --------------------
local = True   # True = input/*.csv | False = live ophalen bij CBS StatLine


# %% 1. Data inlezen -----------------------------------------------------
datasets = data_loader.load_all(local=local)
print(f"Data ingelezen. Bron: {datasets.bron}")


# %% 2. Analyse: standaardmethode + eigen scenario -----------------------
results = analysis.run_all(datasets)


# %% 3. Rapport bouwen (grafieken + HTML) ---------------------------------
html = report.build_report(datasets, results)


# %% 4. Wegschrijven naar output/ -----------------------------------------
p.OUTPUT_DIR.mkdir(exist_ok=True)
p.REPORT_OUTPUT_PATH.write_text(html, encoding="utf-8")
results["scenario_sterfte"].to_csv(p.SCENARIO_CSV_OUTPUT_PATH, index=False)

print("Klaar.")
print(f"  Rapport: {p.REPORT_OUTPUT_PATH}")
print(f"  Tabel:   {p.SCENARIO_CSV_OUTPUT_PATH}")
