from pathlib import Path
import os, json
import numpy as np
import pandas as pd
REPOSITORY=Path(__file__).resolve().parents[1]
ROOT=Path(os.environ.get('LUNG_OUTPUT_DIR',REPOSITORY/'outputs'))/'figures'
for folder in ['Main_Figures','Supplementary_Figures','data','author_records/qa']:
    (ROOT/folder).mkdir(parents=True,exist_ok=True)
REGIONS=['AFR','AMR','SEAR','EUR','EMR','WPR']
STRATEGIES=['Uniform','Demand-proportional','Minimum-coverage-focused']
NAMES=dict(zip(STRATEGIES,['Uniform','Demand-growth','Minimum-coverage']))
P=json.loads((REPOSITORY/'data/inputs/final_parameters.json').read_text())
def frame(name):
    return pd.read_csv(REPOSITORY/'data/figure_source'/f'{name}.csv')
def save(name,df):
    df.to_csv(ROOT/'data'/f'{name}.csv',index=False)
