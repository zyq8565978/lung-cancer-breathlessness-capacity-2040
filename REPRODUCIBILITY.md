# Reproducibility

The public release is prepared from the completed lung-cancer-only analysis. Numerical model functions are retained; local directory dependencies have been replaced by repository-relative inputs and a single configurable output directory.

## Verification performed

- Complete numerical replay from the four demographic input extracts and service parameters.
- Main fixed-rate model and all existing risk/population sensitivities.
- Independent alternative service-template calculations.
- All three national capacity-allocation rules, including the national growth-cap sensitivity.
- The complete deterministic robustness grid and committed-budget analyses.
- Opportunity/contact conversions and country-versus-pooled shortfall decomposition.
- Region and income-group aggregation using the released fixed mapping.
- 66 generated reference tables numerically matched within relative tolerance 1e-10 and absolute tolerance 1e-6.

The machine-readable record is `metadata/reproduction_verification.json`. Recorded verification software: Python 3.12.14, NumPy 2.3.5 and pandas 3.0.1. The sensitivity grid is deterministic; counts of scenarios are not probability statements.

## Figure generation

Figures are rendered separately from the released plot-source tables; the numerical replay checks their underlying demographic, service and regional results. Rendering requires the additional packages in `requirements-figures.txt`. PDF/SVG files preserve vector elements. Font substitution may alter layout on systems without Arial.

## External source files

The analysis is reproducible from the included study-specific extracts without a live download. Original WHO/WPP files are separately identified by their source URL, filename, retrieval timestamp and hash. Original source files may be revised at the provider: matching a newer download by filename alone does not establish version equivalence. The extract files in this release are the analysis inputs.

## Result origins

The primary nurse-led service analysis has a 2027 capacity-planning origin. The demographic reference folder additionally retains 2023-origin capacity analyses and the independent Johnson service alternative. Their parameters are not combined with the primary Greer service template. `analysis/service` and `analysis/derived` produce the main delivery/allocation results; `analysis/regional` performs descriptive aggregation of those national outputs.
