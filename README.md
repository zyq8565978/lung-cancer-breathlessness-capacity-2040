# Lung cancer breathlessness service capacity to 2040

Data and analysis code for **Planning nurse-led service capacity for breathlessness near the end of life in lung cancer: A multicountry modelling study to 2040**.

This repository links demographic projections of symptom-related end-of-life populations to a nurse-led service template and national service-capacity planning rules. It contains the source-data extracts, clinical parameters, national results, sensitivity analyses, regional summaries, and source values used for the study figures and tables.

## Study scope

- 183 WHO Member States; adults aged 30 years and older.
- Trachea, bronchus and lung cancers: WHO GHE680, ICD-10 C33-C34.
- Health-estimate baseline: 2023. Service-planning origin: 2027. Endpoint: 2040.
- Historical GHE anchors: 2000, 2010, 2015, 2019, 2020, 2021, 2022 and 2023.
- Primary scenario: constant 2023 country-age-sex mortality rates with UN WPP2024 populations. A damped historical-risk scenario provides sensitivity analysis.
- The modelled population is annual lung-cancer decedents who experienced breathlessness during their last year of life. The service outputs are conditional planning quantities, rather than observed service use or intervention effects.

## Reproduce the analysis

The numerical analysis uses Python 3.12, NumPy and pandas. The original recorded environment is Python 3.12.14, NumPy 2.3.5 and pandas 3.0.1.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell, instead:
# .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python reproduce.py
```

For the full deterministic sensitivity grid:

```bash
python reproduce.py --include-robustness
```

For file-integrity verification alone:

```bash
python reproduce.py --check-only
```

The runner starts from `data/inputs`, recomputes the model and descriptive summaries, and compares generated numerical tables with the published reference values. It writes results to `outputs/` without altering the supplied data. A successful run produces `outputs/reproduction_check.json`. Numerical tolerances are 1e-10 relative and 1e-6 absolute, allowing floating-point and CSV round-trip differences. Compressed-file hashes themselves need not match after recompression.

## Contents

| Directory | Contents |
| --- | --- |
| `data/inputs/` | Country-level source-data extracts, population series, service parameters, and fixed region/income mapping |
| `data/reference/demographic/` | Population and mortality scenarios, backcasts, decomposition, and independent Johnson service-template calculations |
| `data/reference/service/` | Greer-template service delivery, national allocation results, and sensitivity scenarios |
| `data/reference/derived/` | Offer/contact target conversion and total versus distribution-related shortfalls |
| `data/figure_source/` | Numeric source tables for main and supplementary figures and tables |
| `analysis/` | Reproducible numerical models and descriptive aggregation |
| `visualisation/` | Main and supplementary figure plotting source |
| `metadata/` | Original-source URLs and hashes, parameter provenance, data dictionary, and file inventory |

## Definitions

The symptom-related population is `N = deaths * p`, with an external reference `p = 0.78`. The service-applicable population is `E = e * N`; reference applicability is `e = 0.50`. Reference offer coverage is `q_offer = 0.50` of E.

First- and second-contact attendance are 106/126 and 93/126 of participants allocated to the nurse-led intervention. Expected second contacts are `O * 93/126`, where O is the offered population. The second-contact proportion is also a sequential-course completion proxy; joint attendance is bounded by 73/126 to 93/126. The two contact proportions are not multiplied together.

Reference specified hours per offered person are:

```text
h = (106/126 + 93/126) * (37.5 + 10)/60 + 15/60
```

This includes delivered-contact time, documentation and coordination. Other activities are not included in this coefficient.

Annual additional capacity follows one of three rules: **Uniform**, **Demand-growth**, and **Minimum-coverage**. The last uses water-level filling. These are national annual allocation rules with a common total budget. Regional outputs aggregate the same national allocations; they do not rerun allocation within regions. Internal CSV labels `Demand-proportional` and `Minimum-coverage-focused` correspond to the latter two display names.

The main service-planning calculations begin in 2027. The demographic directory also retains 2023-origin capacity calculations and the separate Johnson service template for sensitivity and supplementary reporting; these have distinct origins and contact assumptions.

## Figures and tables

```bash
python -m pip install -r requirements-figures.txt
python reproduce.py --figures
```

The plotting code reads the released `data/figure_source` tables. It does not refit a model while drawing. Main Figures 1-3 and supplementary figures are written as editable PDF/SVG and 600-dpi PNG. Arial is used when installed; Matplotlib's fallback font is used otherwise. Figure source files retain identifiers from their original generation; the plotting script and `metadata/file_inventory.csv` identify current use. `Table_1_values.csv` and `Table_2_values.csv` hold main-table numerical values. Supplementary source tables use the `S2_` to `S6_` prefixes; definitions and parameters are provided separately in `metadata/parameter_sources.csv` and the data dictionary.

## Data sources and reuse

Source data are publicly available from [WHO Global Health Estimates](https://www.who.int/data/global-health-estimates) and [UN World Population Prospects 2024](https://population.un.org/wpp/). Country classification sources are recorded in the mapping file. Exact download URLs, archived source filenames, access timestamps and SHA-256 hashes are listed in `metadata/original_sources.csv`.

This repository distributes study-specific extracts and derived results, not the complete original WHO/WPP source files or clinical-paper full texts. Extracted death counts are expressed in persons after conversion from the source units. See [DATA_SOURCES.md](DATA_SOURCES.md) for attribution and third-party terms. The projections and service scenarios are the study authors' calculations, not official WHO or UN forecasts of nursing-service demand.

## Citation

Use the manuscript title above and this repository's release tag and commit identifier when citing the analysis. No publication DOI or repository DOI is assigned in this release.

Repository: https://github.com/zyq8565978/lung-cancer-breathlessness-capacity-2040
