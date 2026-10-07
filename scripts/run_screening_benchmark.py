#!/usr/bin/env python
from pathlib import Path
import argparse, json, sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from synthsift.screening import repeated_oof_scores,evaluate_scores,workload_at_recall,bootstrap_ci

p=argparse.ArgumentParser()
p.add_argument('--all-records',action='store_true',help='include rows without verified source-authored text')
p.add_argument('--repeats',type=int,default=10)
p.add_argument('--output',default=str(ROOT/'results/screening_results.json'))
a=p.parse_args()
df=pd.read_csv(ROOT/'data/records.csv')
if not a.all_records: df=df[df.primary_benchmark==1].copy()
texts=(df.title.fillna('')+'. '+df.screening_text.fillna('')).tolist(); y=df.reference_label.astype(int).to_numpy()
models=['word_tfidf_logreg','char_tfidf_logreg']
out={'scope':'all_records' if a.all_records else 'provenance_clean','n':len(df),'included':int(y.sum()),'excluded':int(len(y)-y.sum()),'models':{}}
for model in models:
    scores=repeated_oof_scores(texts,y,model,n_splits=5,n_repeats=a.repeats)
    r=evaluate_scores(y,scores,name=model)
    false_neg=df.loc[(y==1)&(r.predictions==0),['id','title']].to_dict('records')
    out['models'][model]={
      'precision':r.precision,'recall':r.recall,'f1':r.f1,'confusion_matrix':r.confusion,
      'ci95':{m:bootstrap_ci(y,r.predictions,m) for m in ['precision','recall','f1']},
      'false_negatives':false_neg,
      'workload':{str(t):workload_at_recall(y,scores,t) for t in [0.90,0.95,1.0]},
      'scores':dict(zip(df.id.tolist(),map(float,scores)))
    }
Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
