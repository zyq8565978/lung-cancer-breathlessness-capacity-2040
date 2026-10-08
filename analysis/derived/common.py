from pathlib import Path
import os, json, hashlib
import numpy as np
import pandas as pd

REPOSITORY = Path(__file__).resolve().parents[2]
OUTPUT = Path(os.environ.get('LUNG_OUTPUT_DIR', REPOSITORY/'outputs'))
ROOT = OUTPUT/'derived'
for folder in ['data','results','logs']:
    (ROOT/folder).mkdir(parents=True, exist_ok=True)

def log(step, detail):
    print(step, detail)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(df, name):
    df.to_csv(ROOT/'results'/name, index=False)

def read(name):
    return pd.read_csv(ROOT/'results'/name)

STRATEGIES=['Uniform','Demand-proportional','Minimum-coverage-focused']
def service(name):
    return pd.read_csv(OUTPUT/'service/results'/name)
def result(name):
    return read(name)
