#!/usr/bin/env python
from pathlib import Path
import json, sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from synthsift.extraction import extract_country,extract_study_design,extract_sample_size
rec=pd.concat([pd.read_csv(p) for p in sorted((ROOT/'data/records').glob('records_*.csv'))],ignore_index=True).set_index('id')
ref=pd.read_csv(ROOT/'data/extraction_reference.csv').fillna('')
rows=[]
for _,r in ref.iterrows():
    txt=str(rec.loc[r.id,'title'])+'. '+str(rec.loc[r.id,'screening_text'])
    pred={'country':extract_country(txt),'study_design':extract_study_design(txt),'sample_size':extract_sample_size(txt) or ''}
    rows.append({'id':r.id,**{f'ref_{k}':r[k] for k in ['country','study_design','sample_size']},**{f'pred_{k}':v for k,v in pred.items()}})
outdf=pd.DataFrame(rows)
metrics={}
for field in ['country','study_design','sample_size']:
    mask=outdf[f'ref_{field}'].astype(str)!=''
    if field == 'sample_size':
        ref_norm=pd.to_numeric(outdf.loc[mask,f'ref_{field}'],errors='coerce')
        pred_norm=pd.to_numeric(outdf.loc[mask,f'pred_{field}'],errors='coerce')
        em=float((ref_norm==pred_norm).mean()) if mask.any() else None
    else:
        em=float((outdf.loc[mask,f'ref_{field}'].astype(str)==outdf.loc[mask,f'pred_{field}'].astype(str)).mean()) if mask.any() else None
    metrics[field]={'n_reference':int(mask.sum()),'exact_match':em}
out={'metrics':metrics,'records':outdf.to_dict('records')}
(ROOT/'results').mkdir(exist_ok=True)
(ROOT/'results/extraction_results.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
outdf.to_csv(ROOT/'results/extraction_predictions.csv',index=False)
print(json.dumps(metrics,indent=2))
