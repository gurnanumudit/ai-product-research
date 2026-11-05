"""Reviewed whole-family completed-outcome bootstrap helper; no I/O."""
import numpy as np
def require(test,msg):
 if not test: raise RuntimeError(msg)
def compute(rows,draws):
 fams=sorted(set(r['family_id'] for r in rows));require(len(fams)==30,'family count')
 totals=[];counts=[]
 for fid in fams:
  group=[r for r in rows if r['family_id']==fid];require(len(group)==6,'six assignments per family/start')
  require({(r['orientation'],r['repetition']) for r in group}=={(o,k) for o in ('original','mirror') for k in (1,2,3)},'family design')
  known=[r for r in group if r['status']=='completed'];totals.append(sum(r['gap'] for r in known));counts.append(len(known))
 totals=np.array(totals);counts=np.array(counts);den=counts[draws].sum(axis=1);require(np.all(den>0),'empty bootstrap sample')
 samples=totals[draws].sum(axis=1)/den
 return float(totals.sum()/counts.sum()),[float(x) for x in np.quantile(samples,[.025,.975],method='linear')],fams
