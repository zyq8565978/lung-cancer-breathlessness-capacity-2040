"""Reproduce the national model, descriptive summaries, and saved figures."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent
ROBUST = {'robust_scenarios.csv.gz', 'robust_summary.csv', 'committed_budget_stress.csv'}


def verify_checksums():
    manifest = ROOT/'metadata/checksums.csv'
    if not manifest.exists():
        raise FileNotFoundError(manifest)
    entries = pd.read_csv(manifest)
    for row in entries.itertuples():
        path = ROOT/row.path
        if hashlib.sha256(path.read_bytes()).hexdigest() != row.sha256:
            raise ValueError(f'Checksum mismatch: {row.path}')
    print(f'Verified {len(entries)} input and reference file checksums.', flush=True)


def compare_file(actual, reference):
    a, b = pd.read_csv(actual), pd.read_csv(reference)
    pd.testing.assert_frame_equal(a, b, check_dtype=False, check_exact=False,
                                  rtol=1e-10, atol=1e-6)
    return {'reference': str(reference.relative_to(ROOT)).replace('\\', '/'),
            'rows': len(b), 'columns': len(b.columns), 'matched': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-robustness', action='store_true',
                        help='Also recompute the full deterministic sensitivity grid.')
    parser.add_argument('--figures', action='store_true',
                        help='Render publication figures from the released plotting tables.')
    parser.add_argument('--check-only', action='store_true', help='Verify file checksums only.')
    parser.add_argument('--output', type=Path, default=ROOT/'outputs')
    args = parser.parse_args()
    verify_checksums()
    if args.check_only:
        return
    output = args.output.resolve()
    if output == ROOT or ROOT.is_relative_to(output):
        raise ValueError('Output must not be the repository or its parent.')
    for component in ['demographic', 'service', 'derived']:
        (output/component/'data').mkdir(parents=True, exist_ok=True)
    for name in ['lung_deaths_anchors.csv', 'population_WPP2024.csv',
                 'population_GHE.csv', 'country_ledger.csv']:
        shutil.copy2(ROOT/'data/inputs'/name, output/'demographic/data'/name)
    for component in ['service', 'derived']:
        shutil.copy2(ROOT/'data/inputs/service_parameters.json',
                     output/component/'data/service_parameters.json')
    env = os.environ.copy()
    env['LUNG_OUTPUT_DIR'] = str(output)
    env['PYTHONUTF8'] = '1'
    scripts = ['demographic/model_lung.py', 'demographic/capacity_and_services.py',
               'service/service_model.py']
    if args.include_robustness:
        scripts.append('service/robustness.py')
    scripts += ['derived/derive_results.py', 'regional/aggregate.py']
    for script in scripts:
        print(f'Running {script}', flush=True)
        subprocess.run([sys.executable, str(ROOT/'analysis'/script)],
                       env=env, cwd=ROOT, check=True)
    matches = []
    for reference in sorted((ROOT/'data/reference').glob('*/*.csv*')):
        if reference.name in ROBUST and not args.include_robustness:
            continue
        actual = output/reference.parent.name/'results'/reference.name
        matches.append(compare_file(actual, reference))
    for actual in sorted((output/'regional/results').glob('*.csv')):
        reference = ROOT/'data/figure_source'/actual.name
        if reference.exists():
            matches.append(compare_file(actual, reference))
    report = {'python': sys.version.split()[0],
              'packages': {p: importlib.metadata.version(p) for p in ['numpy', 'pandas']},
              'full_sensitivity_grid': args.include_robustness,
              'comparisons': matches, 'tolerance': {'relative': 1e-10, 'absolute': 1e-6}}
    (output/'reproduction_check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'Matched {len(matches)} reference tables.', flush=True)
    if args.figures:
        subprocess.run([sys.executable, str(ROOT/'visualisation/plot_figures.py')],
                       env=env, cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
