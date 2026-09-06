# main.R
# --------------------------------------------------------------
# Startpunt van het project.
# 1. Data inlezen
# 2. Analyse: standaardmethode + eigen scenario
# 3. Rapport bouwen (grafieken + HTML) 
# 4. Wegschrijven naar output/ 

source("utils/parameters.R")
source("utils/data_loader.R")
source("utils/analysis.R")
source("utils/visuals.R")
source("utils/report.R")

# %% Instelling: lokale CSV's of live CBS StatLine? ------------------------
local <- TRUE   # TRUE = input/*.csv | FALSE = live ophalen bij CBS StatLine


# %% 1. Data inlezen --------------------------------------------------------
datasets <- load_all(local = local)
cat("Data ingelezen. Bron:", datasets$bron, "\n")


# %% 2. Analyse: standaardmethode + eigen scenario --------------------------
results <- run_all(datasets)


# %% 3. Rapport bouwen (grafieken + HTML) ------------------------------------
html <- build_report(datasets, results)


# %% 4. Wegschrijven naar output/ ---------------------------------------------
if (!dir.exists(OUTPUT_DIR)) dir.create(OUTPUT_DIR)
writeLines(html, REPORT_OUTPUT_PATH, useBytes = TRUE)
write.csv(results$scenario_sterfte, SCENARIO_CSV_OUTPUT_PATH, row.names = FALSE)

cat("Klaar.\n")
cat("  Rapport:", REPORT_OUTPUT_PATH, "\n")
cat("  Tabel:  ", SCENARIO_CSV_OUTPUT_PATH, "\n")
