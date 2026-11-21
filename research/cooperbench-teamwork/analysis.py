"""Reviewed pure analysis, extracted verbatim; no collector, grade or report entrypoint.
The actual incomplete-study path disables resampling. See PROVENANCE.md.
"""
import collections, math, random, statistics
N = 333
ARMS = ['SOLO', 'SIMPLE', 'STRUCTURED']
SEED = 20261109
RESAMPLES = 20000

def require(ok, message):
    if not ok:
        raise ValueError(message)

def ratio(a,b):return a/b if b else None

def percentile(xs,q):
    ys=sorted(xs);p=(len(ys)-1)*q;i=int(p);j=min(i+1,len(ys)-1)
    return ys[i]+(ys[j]-ys[i])*(p-i)

def interval(xs):
    missing=sum(x is None for x in xs)
    return dict(low=None if missing else percentile(xs,.025),high=None if missing else percentile(xs,.975),undefined_resamples=missing,resamples=len(xs))

def base_id(r):return (r['repo'],r['task_id'])

def mean(xs):return statistics.mean(xs) if xs else None

def validate_rows(rows,tasks):
    seen=set()
    for r in rows:
        require(type(r['ti']) is int and r['ti'] in tasks and type(r['rep']) is int and 0<=r['rep']<3 and r['arm'] in ARMS,'row slot')
        key=(r['ti'],r['rep'],r['arm']);require(key not in seen,'duplicate row');seen.add(key)
        t=tasks[r['ti']]
        require(all(r[k]==t[k] for k in ['repo','task_id','features','previously_run_base']),'row task identity')
        require(type(r['features_credit']) is int and 0<=r['features_credit']<=2 and type(r['both']) is int and r['both']==int(r['features_credit']==2),'score values')
        require(r['agents']==(1 if r['arm']=='SOLO' else 2),'agent denominator')
        require(type(r['calls']) is int and 0<=r['calls']<=32,'calls')
        for k in ['api_usd','wall_seconds','grade_seconds']:
            require(type(r[k]) in [int,float] and math.isfinite(r[k]) and r[k]>=0,'numeric '+k)
        phases={'solo'} if r['arm']=='SOLO' else {'simple'} if r['arm']=='SIMPLE' else {'plan','build','integrate'}
        require(set(r['phases'])==phases,'phase set')
        require(sum(p['calls'] for p in r['phases'].values())==r['calls'],'phase calls')
        require(abs(sum(p['api_usd'] for p in r['phases'].values())-r['api_usd'])<1e-8,'phase costs')
        for k,p in r['phases'].items():require(0<=p['calls']<=dict(solo=32,simple=32,plan=4,build=20,integrate=8)[k],'phase allowance')
    return seen

def weighted_summary(rows,tasks,metric,fill,ids=None):
    lookup={(r['ti'],r['rep'],r['arm']):r for r in rows};bybase=collections.defaultdict(list)
    for ti,t in tasks.items():
        if ids is None or ti in ids:bybase[base_id(t)].append(ti)
    result={}
    for arm in ARMS:
        vals=[]
        for ids in bybase.values():
            pairs=[]
            for ti in ids:
                values=[]
                for rep in range(3):
                    r=lookup.get((ti,rep,arm));v=fill if r is None else r[metric]
                    values.append(v)
                pairs.append(mean(values))
            vals.append(mean(pairs))
        result[arm]=mean(vals)
    return result

def complete_stratum(rows,tasks,ids,draws=RESAMPLES):
    base_to_tis=collections.defaultdict(list)
    for ti in ids:base_to_tis[base_id(tasks[ti])].append(ti)
    bases=sorted(base_to_tis);repos=sorted({b[0] for b in bases});repo_ids=[[i for i,b in enumerate(bases) if b[0]==repo] for repo in repos]
    bycell=collections.defaultdict(list)
    for r in rows:
        if r['ti'] in ids:bycell[(r['ti'],r['arm'])].append(r)
    val={a:[] for a in ARMS};credit={a:[] for a in ARMS};cost={a:[] for a in ARMS};success={a:[] for a in ARMS};counts=[]
    for b in bases:
        tis=base_to_tis[b];counts.append(len(tis)*3)
        for a in ARMS:
            require(all(len(bycell[(ti,a)])==3 for ti in tis),'complete stratum missing cell')
            val[a].append(mean([mean([r['both'] for r in bycell[(ti,a)]]) for ti in tis]))
            credit[a].append(mean([mean([r['features_credit'] for r in bycell[(ti,a)]]) for ti in tis]))
            cost[a].append(sum(r['api_usd'] for ti in tis for r in bycell[(ti,a)]))
            success[a].append(sum(r['both'] for ti in tis for r in bycell[(ti,a)]))
    rng=random.Random(SEED);task_draws=[[rng.randrange(len(bases)) for _ in bases] for _ in range(draws)]
    rng=random.Random(SEED);repo_draws=[[i for _ in repos for i in repo_ids[rng.randrange(len(repos))]] for _ in range(draws)]
    arms={a:dict(base_weighted_success=mean(val[a]),base_weighted_features=mean(credit[a]),base_weighted_features_per_agent=mean(credit[a])/(1 if a=='SOLO' else 2)) for a in ARMS}
    contrasts=[]
    for a,b in [('STRUCTURED','SOLO'),('STRUCTURED','SIMPLE')]:
        delta=[x-y for x,y in zip(val[a],val[b])]
        contrasts.append(dict(comparison=a+' minus '+b,estimate=mean(delta),task_interval=interval([mean([delta[i] for i in d]) for d in task_draws]),repository_sensitivity=interval([mean([delta[i] for i in d]) for d in repo_draws]),leave_one_repository_out={repo:mean([delta[i] for i,base in enumerate(bases) if base[0]!=repo]) for repo in repos}))
    for a in ARMS:
        arms[a]['api_per_success_task_interval']=interval([ratio(sum(cost[a][i] for i in d),sum(success[a][i] for i in d)) for d in task_draws])
        arms[a]['api_per_success_repository_interval']=interval([ratio(sum(cost[a][i] for i in d),sum(success[a][i] for i in d)) for d in repo_draws])
    return dict(base_tasks=len(bases),repositories=len(repos),pairs=len(ids),arms=arms,contrasts=contrasts,seed=SEED,resamples=draws,interpretation='Exploratory unadjusted resampling under exchangeability assumptions; not a representative sample of all coding work. Degenerate intervals are not proof of population certainty.')

def analyze(rows,tasks,draws=RESAMPLES,interrupted_costs=None):
    validate_rows(rows,tasks);require(len(rows)<=327,'six permanently missing: no full-data CI');complete=False;out=dict(complete=complete,assigned=N,observed=len(rows),missing=N-len(rows),arms={})
    low=weighted_summary(rows,tasks,'both',0);high=weighted_summary(rows,tasks,'both',1)
    fl=weighted_summary(rows,tasks,'features_credit',0);fh=weighted_summary(rows,tasks,'features_credit',2)
    for a in ARMS:
        rs=[r for r in rows if r['arm']==a];n=len(rs);b=sum(r['both'] for r in rs);f=sum(r['features_credit'] for r in rs);completed_cost=sum(r['api_usd'] for r in rs);aborted=(interrupted_costs or {}).get(a,dict(settled_calls=0,settled_nano_usd=0));cost=completed_cost+aborted['settled_nano_usd']/1e9
        phases={}
        for r in rs:
            for phase,p in r['phases'].items():
                q=phases.setdefault(phase,{k:0 for k in ['calls','api_usd','wall_seconds','shell_actions','messages','messages_delivered']})
                for k in q:q[k]+=p[k]
        agents=1 if a=='SOLO' else 2
        out['arms'][a]=dict(assigned=111,observed=n,successes=b,features=f,missing=111-n,raw_success_bounds=[b/111,(b+111-n)/111],base_weighted_success_bounds=[low[a],high[a]],base_weighted_feature_bounds=[fl[a],fh[a]],completed_only_rate=ratio(b,n),completed_only_features_per_team=ratio(f,n),completed_only_features_per_agent=ratio(f,n*agents),api_usd=cost,completed_api_usd=completed_cost,interrupted_api_usd=aborted['settled_nano_usd']/1e9,interrupted_calls=aborted['settled_calls'],unknown_requests=aborted.get('unknown_requests',0),unknown_reserve_usd=aborted.get('unknown_reserve_nano_usd',0)/1e9,api_plus_unknown_reserve_per_observed_success=ratio(cost+aborted.get('unknown_reserve_nano_usd',0)/1e9,b),api_per_observed_success=ratio(cost,b),api_plus_assigned_allowance_per_observed_success=ratio(cost+5/3,b),api_plus_observed_allowance_per_observed_success=ratio(cost+5*n/len(rows),b) if rows else None,phases=phases,calls=sum(r['calls'] for r in rs),messages=sum(r['messages'] for r in rs),messages_delivered=sum(r['messages_delivered'] for r in rs),summed_team_seconds=sum(r['wall_seconds'] for r in rs),merge_status_counts=dict(collections.Counter((r.get('merge') or {}).get('status','single_patch') for r in rs)),integration_status_counts=dict(collections.Counter(r.get('integration_setup') for r in rs)))
    out['base_weighted_contrast_missing_bounds']={a+' minus '+b:[low[a]-high[b],high[a]-low[b]] for a,b in [('STRUCTURED','SOLO'),('STRUCTURED','SIMPLE')]}
    out['strata']={}
    for label,exposed in [('unrun_bases',False),('previously_run_bases',True)]:
        ids=[i for i,t in tasks.items() if t['previously_run_base'] is exposed]
        lo=weighted_summary(rows,tasks,'both',0,ids);hi=weighted_summary(rows,tasks,'both',1,ids)
        flo=weighted_summary(rows,tasks,'features_credit',0,ids);fhi=weighted_summary(rows,tasks,'features_credit',2,ids)
        s=dict(base_tasks=len({base_id(tasks[i]) for i in ids}),pairs=len(ids),assigned_per_arm=3*len(ids),arms={})
        for arm in ARMS:
            rs=[r for r in rows if r['ti'] in ids and r['arm']==arm];n=len(rs);b=sum(r['both'] for r in rs);f=sum(r['features_credit'] for r in rs)
            s['arms'][arm]=dict(observed=n,missing=s['assigned_per_arm']-n,successes=b,features=f,completed_only_rate=ratio(b,n),completed_only_features_per_team=ratio(f,n),completed_only_features_per_agent=ratio(f,n*(1 if arm=='SOLO' else 2)),base_weighted_success_bounds=[lo[arm],hi[arm]],base_weighted_feature_bounds=[flo[arm],fhi[arm]])
        s['contrast_missing_bounds']={a+' minus '+b:[lo[a]-hi[b],hi[a]-lo[b]] for a,b in [('STRUCTURED','SOLO'),('STRUCTURED','SIMPLE')]}
        out['strata'][label]=s
    out['resampling']=None
    if complete:
        out['resampling']={'all':complete_stratum(rows,tasks,list(tasks),draws)}
        for label,exposed in [('unrun_bases',False),('previously_run_bases',True)]:
            out['resampling'][label]=complete_stratum(rows,tasks,[i for i,t in tasks.items() if t['previously_run_base'] is exposed],draws)
    return out
