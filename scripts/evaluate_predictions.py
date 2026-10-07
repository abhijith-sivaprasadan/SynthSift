#!/usr/bin/env python
"""Evaluate external/LLM screening predictions without coupling SynthSift to a vendor API.

Expected CSV columns: id,score where score is a numeric probability/ranking score for inclusion.
"""
from pathlib import Path
import argparse, json, sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from synthsift.screening import evaluate_scores, workload_at_recall
p=argparse.ArgumentParser(); p.add_argument('predictions'); p.add_argument('--threshold',type=float,default=.5); a=p.parse_args()
ref=pd.read_csv(ROOT/'data/records.csv'); ref=ref[ref.primary_benchmark==1][['id','reference_label','title']]
pred=pd.read_csv(a.predictions)[['id','score']]
df=ref.merge(pred,on='id',how='inner',validate='one_to_one')
r=evaluate_scores(df.reference_label,df.score,a.threshold,'external')
print(json.dumps({'n':len(df),'precision':r.precision,'recall':r.recall,'f1':r.f1,'confusion_matrix':r.confusion,'workload':{str(t):workload_at_recall(df.reference_label,df.score,t) for t in [.9,.95,1.0]}},indent=2))
