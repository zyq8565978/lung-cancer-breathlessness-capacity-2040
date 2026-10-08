# Data sources and attribution

## WHO Global Health Estimates

World Health Organization. Global Health Estimates, 2023 estimates (release files dated 1 October 2026). Country-age-sex mortality estimates and population denominators. The source files used were accessed on 2 October 2026. Exact URLs and hashes are in `metadata/original_sources.csv`.

The study extracts concern trachea, bronchus and lung cancers (GHE680/C33-C34), adults aged 30 years and older. Age groups are 30-49, 50-59, 60-69 and 70+. Source row/column locations, filenames and units accompany the death extracts. Values are estimates; `deaths` is in persons, with source values converted from thousands where applicable.

[Source portal](https://www.who.int/data/global-health-estimates) | [WHO data terms](https://www.who.int/about/policies/publishing/data-policy/terms-and-conditions).

WHO retains rights in its data. Attribute WHO when reusing the extracts. The study-specific selection, harmonisation and calculations are identified as such and do not imply WHO endorsement.

## UN World Population Prospects 2024

United Nations, Department of Economic and Social Affairs, Population Division. World Population Prospects 2024, medium variant. The study extract contains annual population counts for the included countries, sex categories and age groups. Source attribution and reuse remain subject to UN terms, including the stated CC BY 3.0 IGO terms where applicable to the source product.

[Source portal](https://population.un.org/wpp/) | [2024 source documentation](https://www.un.org/development/desa/pd/content/wpp2024-data-sources).

## Country classifications

WHO region membership is held constant across all years using the saved mapping. World Bank income groups use FY2024 (effective July 2023), as documented in the country mapping. These groupings are descriptive and do not alter the 183-country analysis set. Original classification URLs accompany the mapping.

## Clinical parameters

| Parameter family | Source | Use |
| --- | --- | --- |
| Breathlessness symptom reference | Edmonds et al. (2001), DOI [10.1191/026921601678320278](https://doi.org/10.1191/026921601678320278) | External reference proportion of 0.78; deterministic sensitivity analysis |
| Nurse-led service contacts | Greer et al., DOI [10.1200/JCO.24.00048](https://doi.org/10.1200/JCO.24.00048) | Contact attendance margins and 30-45 minute contact-duration range |
| Separate one-/three-visit service alternative | Johnson et al. (2015), DOI [10.1186/s12916-015-0453-x](https://doi.org/10.1186/s12916-015-0453-x) | Independent alternative service template |
| Telephone duration for the alternative template | BREEZE-IPF, DOI [10.1136/bmjresp-2024-002327](https://doi.org/10.1136/bmjresp-2024-002327) | Borrowed duration for a similar activity in another disease |

Clinical full texts are not redistributed. Applicability, target coverage, documentation time, coordination time and capacity-growth assumptions are planning inputs, identified separately from trial-reported quantities in the parameter files.

## Code and derived data

The authors have made the code and study data publicly accessible for inspection and research reproducibility. This release does not assign a blanket open-source licence to third-party data or imply ownership of the original source products. No separate software-reuse licence has yet been specified by the repository owner; contact the owner about uses requiring additional permission.
