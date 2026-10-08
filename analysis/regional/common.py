from pathlib import Path
import os, json
import numpy as np
import pandas as pd
REPOSITORY=Path(__file__).resolve().parents[2]
OUTPUT=Path(os.environ.get('LUNG_OUTPUT_DIR',REPOSITORY/'outputs'))
ROOT=OUTPUT/'regional'
(ROOT/'results').mkdir(parents=True,exist_ok=True)
REGIONS=['AFR','AMR','SEAR','EUR','EMR','WPR']
P=json.loads((OUTPUT/'derived/results/final_parameters.json').read_text())
def read(name):
    component='service' if name=='allocation_country.csv.gz' else 'demographic'
    return pd.read_csv(OUTPUT/component/'results'/name)
def save(name,df):
    df.to_csv(ROOT/'results'/f'{name}.csv',index=False)
