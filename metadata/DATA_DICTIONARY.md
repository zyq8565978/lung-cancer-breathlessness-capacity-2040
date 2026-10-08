# Data dictionary

CSV files use UTF-8 and a dot as the decimal separator. Empty numeric fields denote missing or inapplicable values. CSV.GZ files are gzip-compressed CSV. Values are unrounded unless a field explicitly denotes a formatted display value. Fractional person counts represent model expectations.

`file_inventory.csv` lists file sizes and table dimensions. `column_inventory.csv` enumerates all columns, inferred types and missing-value counts. `checksums.csv` records SHA-256 for all released data files. `original_sources.csv` refers to the original external source files, not local files included in this repository.

## Inputs and identifiers

| Field | Definition or unit |
| --- | --- |
| ISO3 | Three-letter country identifier; used for joins |
| country | Country label carried from the source |
| year | Calendar year |
| age | 30-49, 50-59, 60-69 or 70+ years |
| sex | Males or Females |
| deaths | Estimated deaths in persons |
| population | Population in persons |
| source_file / source_sheet / source_row / source_column | Original GHE extraction location |
| original_unit | Units in the source file, before conversion |
| cause / ghe_code | lung_cancer / GHE680 |
| legacy182 / revised_common183 | Country-membership indicators for the original 182-country sensitivity subset and the 183-country main sample, respectively |
| WHO_region | AFR, AMR, SEAR, EUR, EMR or WPR; constant assignment over time |
| World_Bank_income_group | World Bank FY2024 income category |
| group | WHO region, income category or ALL (all included countries) |

The country ledger also retains source-reconciliation fields for population denominators and Togo's inclusion. These are provenance flags, not modelled clinical outcomes.

## Health and population scenarios

| Field or value | Definition |
| --- | --- |
| fixed_WPP | Constant 2023 age-sex-country mortality rates, WPP population projection |
| damped_risk_WPP | Historical risk slope capped at +/-0.05/year and damped with a 10-year half-life |
| GHE_baseline_WPP_future_sensitivity | Alternative baseline population-denominator sensitivity |
| death_rate | Deaths divided by population, without a per-1000 multiplier |
| symptom_people / people | Modelled symptom-related population, after application of p |
| p | Symptom reference proportion, 0.78 in the reference scenario |
| population_size | Shapley contribution of population size aged 30+; symptom-related people |
| age_sex_structure | Shapley contribution of age-sex composition; symptom-related people |
| mortality_risk | Shapley contribution of group-specific mortality risk; symptom-related people |
| total_change | Difference between compared endpoints; sum of the three contributions |
| origin / target | Starting and ending anchor years of a backcast |
| WAPE | Sum absolute backcast errors divided by sum reference deaths; a fraction |

## Service delivery

| Field | Definition or unit |
| --- | --- |
| e | Fraction of the symptom-related population applicable to the service |
| eligible | Service-applicable population E = eN |
| q / q_offer | Target fraction of E offered a service opportunity |
| offered | Capacity-constrained offered population O |
| first / second (parameters) | Trial attendance margins, 106 and 93 out of 126 allocated participants |
| started / first_contacts | Expected first-contact attendees or contacts |
| completed / course_proxy_completed | Expected second-contact attendees, interpreted as sequential completion proxy |
| joint_completion | Both-contact completion proportion used for a bound or proxy scenario |
| duration | Minutes per delivered contact |
| documentation_minutes | Documentation minutes per delivered contact |
| coordination_minutes | Coordination minutes per offered person |
| specified_hours | Hours of the explicitly enumerated service activities |
| required_q_offer | Offer fraction required algebraically for the stated target |
| feasible | Whether a requested completion target needs no more than 100% offer coverage |
| completion_scenario | Attendance sensitivity setting; Low and High use bounds of trial margins, not a complete model uncertainty interval |

Raw proportions are fractions (0 to 1). Columns ending in `_pct` or `_pct_target` are percentages (0 to 100). Per-1000 outputs name their denominator explicitly: eligible, offered, or second-contact/completion proxy.

## National capacity and allocation

| Field | Definition or unit |
| --- | --- |
| risk | Demographic/risk scenario identifier |
| strategy | Uniform; Demand-proportional (display: Demand-growth); Minimum-coverage-focused (display: Minimum-coverage) |
| annual_growth | Annual growth in total service-hour capacity as a fraction |
| local_cap | National new-capacity growth constraint, or unconstrained new capacity |
| allocated_hours | Annual service-hour capacity assigned to countries |
| coverage / weighted_coverage | Offered / eligible, country-specific or pooled weighted fraction |
| shortfall / L_country | Sum of national positive target shortfalls, in service opportunities |
| pooled_shortfall / L_pooled | Theoretical lower bound under fully poolable capacity |
| L_distribution | Additional distribution-related shortfall: L_country minus L_pooled |
| countries_below | Number of countries below the offer target |
| cumulative_shortfall | Sum of annual positive opportunity shortfalls over the planning years to date |
| cum_target_people | Sum of annual target service opportunities to date |

Capacity is persistent within countries; only annual increments follow the three allocation rules. Cumulative opportunity shortfalls concern separate annual death cohorts and are not observed waiting-list counts.

## Main-table and figure sources

`Table_1_values.csv` and `regional_population.csv` summarise populations and reference target hours by region; `Table_2_values.csv` summarises the allocation endpoints. National data remain available separately. `F2C_target_conversion.csv` supplies the two offer-versus-second-contact target comparisons. `F1B_age_sex.csv` supplies the main age-sex panel. Prefixes describe source-table identifiers, not necessarily the current figure-panel letter.

The plotting code records exactly which source files are consumed. Supplementary tables include health-estimate detail (`S2_*`), service parameters and alternatives (`S3_*`), allocation (`S4_*`), backcasts/population sensitivity (`S5_*`), and parameter/budget sensitivity (`S6_*`).
