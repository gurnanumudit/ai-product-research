"""Portable supplementary article analysis; Python 3.10+ standard library.

Reads only package data and emits JSON to stdout. No network or model calls.
Statistical functions and resampling seeds match the saved article analysis.
"""
import collections
import functools
import hashlib
import itertools
import json
import math
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'data/reviews.json'
doc = json.loads(SOURCE.read_text())
MODELS = ['openai/gpt-5.6-terra', 'anthropic/claude-sonnet-5', 'google/gemini-3.8-flash']
METRICS = ['approval_rate', 'correct_patch_approval_rate', 'incorrect_patch_approval_rate', 'approval_precision', 'policy_agreement']
labels = {(r['phase'], r['task_id']): r['resolved'] for r in doc['labels']}
cells = {(r['phase'], r['task_id'], r['model'], r['condition'], r['repeat']): r for r in doc['cells']}
assert len(cells) == 1736 and sum(r['valid'] for r in cells.values()) == 1692


def ratio(n, d):
    return n/d if d else None

def metrics(tp, fp, good, bad):
    return dict(zip(METRICS, [ratio(tp+fp,good+bad), ratio(tp,good), ratio(fp,bad), ratio(tp,tp+fp), ratio(tp+bad-fp,good+bad)]))

@functools.lru_cache(None)
def cp(k,n,alpha):
    """Equal-tail Clopper-Pearson interval via binomial CDF inversion."""
    if not n: return [0.,1.]
    def cdf(x,p):
        return sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(x+1))
    def inverse(x,target):
        lo,hi=0.,1.
        for _ in range(70):
            mid=(lo+hi)/2
            if cdf(x,mid)>target: lo=mid
            else: hi=mid
        return (lo+hi)/2
    return [inverse(k-1,1-alpha/2) if k else 0., inverse(k,alpha/2) if k<n else 1.]

def clustered_interval(approval_counts,alpha=.05):
    """Task mean = .5*(I(any of two)+I(both)). Union bound, no repeat independence."""
    n=len(approval_counts)
    if not n: return None
    a=cp(sum(x>0 for x in approval_counts),n,alpha/2)
    b=cp(sum(x==2 for x in approval_counts),n,alpha/2)
    return [(a[j]+b[j])/2 for j in (0,1)]

def metric_intervals(good_counts,bad_counts):
    g=clustered_interval(good_counts)
    b=clustered_interval(bad_counts)
    # Simultaneous 95% bounds for the two class rates: 97.5% per class.
    gs=clustered_interval(good_counts,.025)
    bs=clustered_interval(bad_counts,.025)
    if not gs or not bs:
        return dict(zip(METRICS,[None,g,b,None,None]))
    w=len(good_counts)/(len(good_counts)+len(bad_counts))
    ap=[w*gs[j]+(1-w)*bs[j] for j in (0,1)]
    pol=[w*gs[0]+(1-w)*(1-bs[1]),w*gs[1]+(1-w)*(1-bs[0])]
    prec=[ratio(w*gs[0],w*gs[0]+(1-w)*bs[1]),ratio(w*gs[1],w*gs[1]+(1-w)*bs[0])]
    return dict(zip(METRICS,[ap,g,b,prec,pol]))

def get(phase,task,model,cond,rep):
    return cells.get((phase,task,model,cond,rep))

def is_complete(phase,task,models,conditions):
    return all((r:=get(phase,task,m,c,i)) and r['valid'] for m in models for c in conditions for i in [1,2])

def count_pair(phase,task,model,cond):
    return sum(get(phase,task,model,cond,i)['decision']=='APPROVE' for i in [1,2])

def stats(phase,tasks,model,condition,complete=False):
    rows=[get(phase,t,model,condition,i) for t in tasks for i in [1,2]]
    attempted=[r for r in rows if r]
    valid=[r for r in attempted if r['valid']]
    good=[r for r in valid if r['resolved']]
    bad=[r for r in valid if not r['resolved']]
    tp=sum(r['decision']=='APPROVE' for r in good)
    fp=sum(r['decision']=='APPROVE' for r in bad)
    ng=sum(labels[phase,t] for t in tasks)
    nb=len(tasks)-ng
    mg,mb=2*ng-len(good),2*nb-len(bad)
    hit=tp+len(bad)-fp
    bounds={
        'approval_rate':[ratio(tp+fp,2*len(tasks)),ratio(tp+fp+mg+mb,2*len(tasks))],
        'correct_patch_approval_rate':[ratio(tp,2*ng),ratio(tp+mg,2*ng)],
        'incorrect_patch_approval_rate':[ratio(fp,2*nb),ratio(fp+mb,2*nb)],
        'approval_precision':[ratio(tp,tp+fp+mb),ratio(tp+mg,tp+mg+fp)],
        'policy_agreement':[ratio(hit,2*len(tasks)),ratio(hit+mg+mb,2*len(tasks))]}
    out=dict(phase=phase,model=model,condition=condition,task_ids=tasks,n_tasks=len(tasks),correct_tasks=ng,incorrect_tasks=nb,planned=len(rows),attempted=len(attempted),usable=len(valid),invalid=len(attempted)-len(valid),unattempted=len(rows)-len(attempted),correct_reviews=len(good),incorrect_reviews=len(bad),correct_approvals=tp,incorrect_approvals=fp,approvals=tp+fp,hold=sum(r['decision']=='HOLD' for r in valid),abstain=sum(r['decision']=='ABSTAIN' for r in valid),policy_agreements=hit,estimate=metrics(tp,fp,len(good),len(bad)),planned_response_bounds=bounds)
    if complete:
        gc=[count_pair(phase,t,model,condition) for t in tasks if labels[phase,t]]
        bc=[count_pair(phase,t,model,condition) for t in tasks if not labels[phase,t]]
        out['interval95']=metric_intervals(gc,bc)
        out['task_approval_counts']={'correct':gc,'incorrect':bc}
    return out

def quantile(xs,p):
    xs=sorted(xs)
    if not xs: return None
    x=(len(xs)-1)*p; lo=math.floor(x); hi=math.ceil(x)
    return xs[lo]+(xs[hi]-xs[lo])*(x-lo)

def comparison(phase,tasks,left,right,name,seed):
    """Paired task bootstrap; class-stratified to keep observed class prevalence fixed."""
    groups=[[t for t in tasks if labels[phase,t]==label] for label in [True,False]]
    lv=[[count_pair(phase,t,*left) for t in group] for group in groups]
    rv=[[count_pair(phase,t,*right) for t in group] for group in groups]
    ng,nb=map(len,groups)
    lm=metrics(sum(lv[0]),sum(lv[1]),2*ng,2*nb)
    rm=metrics(sum(rv[0]),sum(rv[1]),2*ng,2*nb)
    point={k:lm[k]-rm[k] if lm[k] is not None and rm[k] is not None else None for k in METRICS}
    rng=random.Random(seed)
    draws={k:[] for k in METRICS}
    for _ in range(10000):
        ix=[[rng.randrange(len(group)) for __ in group] for group in groups]
        ls=[sum(lv[j][i] for i in ix[j]) for j in [0,1]]
        rs=[sum(rv[j][i] for i in ix[j]) for j in [0,1]]
        a=metrics(*ls,2*ng,2*nb); b=metrics(*rs,2*ng,2*nb)
        for k in METRICS:
            if a[k] is not None and b[k] is not None: draws[k].append(a[k]-b[k])
    leave_repo={}
    for repo in sorted({t.rsplit('-',1)[0] for t in tasks}):
        keep=[t for t in tasks if t.rsplit('-',1)[0]!=repo]
        gs=[t for t in keep if labels[phase,t]]; bs=[t for t in keep if not labels[phase,t]]
        a=metrics(sum(count_pair(phase,t,*left) for t in gs),sum(count_pair(phase,t,*left) for t in bs),2*len(gs),2*len(bs))
        b=metrics(sum(count_pair(phase,t,*right) for t in gs),sum(count_pair(phase,t,*right) for t in bs),2*len(gs),2*len(bs))
        leave_repo[repo]={'n_tasks':len(keep),'correct_tasks':len(gs),'incorrect_tasks':len(bs),'estimate':{k:a[k]-b[k] if a[k] is not None and b[k] is not None else None for k in METRICS}}
    return dict(phase=phase,comparison=name,left=left,right=right,n_tasks=len(tasks),correct_tasks=ng,incorrect_tasks=nb,task_ids=tasks,estimate=point,interval95={k:[quantile(draws[k],.025),quantile(draws[k],.975)] for k in METRICS},bootstrap_valid_draws={k:len(draws[k]) for k in METRICS},bootstrap_seed=seed,bootstrap_degenerate={k:len(set(draws[k]))<=1 for k in METRICS},leave_one_repo=leave_repo)

raw=[]; matched=[]; comparisons=[]; scenario=[]; figure2=[]
for phase in [1,2]:
    tasks=sorted(t for p,t in labels if p==phase)
    for cond in 'ABCDE':
        common=[t for t in tasks if is_complete(phase,t,MODELS,[cond])]
        for model in MODELS:
            raw.append(stats(phase,tasks,model,cond))
            s=stats(phase,common,model,cond,True); matched.append(s)
            for label,field in [('correct','correct_patch_approval_rate'),('incorrect','incorrect_patch_approval_rate')]:
                figure2.append(dict(phase=phase,model=model,condition=cond,label=label,n_tasks=s[label+'_tasks'],n_reviews=s[label+'_reviews'],approvals=s[label+'_approvals'],estimate=s['estimate'][field],interval95=s['interval95'][field],task_ids=[t for t in common if labels[phase,t]==(label=='correct')]))
        for i,(left,right) in enumerate(itertools.combinations(MODELS,2)):
            comparisons.append(comparison(phase,common,(left,cond),(right,cond),left+' minus '+right,20260912+phase*100+ord(cond)*3+i))
    for mi,model in enumerate(MODELS):
        for ci,(left,right) in enumerate([('B','A'),('C','B'),('E','D'),('C','A')]):
            common=[t for t in tasks if is_complete(phase,t,[model],[left,right])]
            scenario.append(comparison(phase,common,(model,left),(model,right),left+' minus '+right,20261912+phase*100+mi*10+ci))

raw_index={(s['phase'],s['model'],s['condition']):s for s in raw}
for comparison_row in comparisons+scenario:
    phase=comparison_row['phase']
    left=raw_index[(phase,*comparison_row['left'])]['planned_response_bounds']
    right=raw_index[(phase,*comparison_row['right'])]['planned_response_bounds']
    comparison_row['planned_roster_completion_bounds']={k:[left[k][0]-right[k][1],left[k][1]-right[k][0]] if all(v is not None for v in left[k]+right[k]) else None for k in METRICS}

assert abs(cp(0,20,.025)[1]-(1-(.025/2)**(1/20)))<1e-12
assert abs(cp(20,20,.025)[0]-(.025/2)**(1/20))<1e-12
assert abs(cp(20,25,.05)[0]-.592962)<1e-6
assert clustered_interval([0]*20)[1]>0

print(json.dumps(dict(source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),analysis_status='SUPPLEMENTARY_POST_HOC_EXISTING_DATA',bootstrap_draws=10000,raw=raw,matched_condition=matched,matched_model_comparisons=comparisons,matched_scenario_comparisons=scenario,figure2=figure2,tests='PASS: input counts, exact binomial boundaries and NIST worked example; archive hashes checked separately'),indent=2))
