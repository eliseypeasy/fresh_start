# requirements.R
# --------------------------------------------------------------
# R kent geen requirements.txt-standaard zoals Python; dit is het
# equivalent. Installeer met:
#
#   Rscript requirements.R
#
# Alleen deze 2 externe packages zijn nodig (en alleen voor de live
# StatLine-koppeling, local = TRUE werkt met kale base R):
#   - jsonlite : JSON parsen (live data) en serialiseren (Plotly-grafieken)
#   - httr     : de HTTP-call naar de CBS StatLine API

pkgs <- c("jsonlite", "httr")
missing <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(missing) > 0) install.packages(missing)
