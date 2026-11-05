"""Offline family-level analysis and design arithmetic. No collection or network I/O."""
import math
import statistics as st

def betacf(a,b,x):
    qab=a+b; qap=a+1; qam=a-1; c=1.; d=1-qab*x/qap
    if abs(d)<1e-300:d=1e-300
    d=1/d; h=d
    for m in range(1,301):
        aa=m*(b-m)*x/((qam+2*m)*(a+2*m))
        d=1+aa*d; c=1+aa/c
        if abs(d)<1e-300:d=1e-300
        if abs(c)<1e-300:c=1e-300
        d=1/d; h*=d*c
        aa=-(a+m)*(qab+m)*x/((a+2*m)*(qap+2*m))
        d=1+aa*d;c=1+aa/c
        if abs(d)<1e-300:d=1e-300
        if abs(c)<1e-300:c=1e-300
        d=1/d;delta=d*c;h*=delta
        if abs(delta-1)<1e-13:return h
    raise ArithmeticError('incomplete beta did not converge')

def ibeta(a,b,x):
    if x<=0:return 0.
    if x>=1:return 1.
    bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    if x<(a+1)/(a+b+2):return bt*betacf(a,b,x)/a
    return 1-bt*betacf(b,a,1-x)/b

def tcdf(t,df):
    if t==0:return .5
    p=.5*ibeta(df/2,.5,df/(df+t*t))
    return 1-p if t>0 else p

def tcrit(df):
    lo,hi=0.,20.
    assert tcdf(hi,df)>.975
    for _ in range(70):
        mid=(lo+hi)/2
        if tcdf(mid,df)<.975:lo=mid
        else:hi=mid
    return (lo+hi)/2

def stratified(values):
    """Equal category weights; independent family means within each category."""
    a,b=[values[k] for k in ('tradeoffs','narrow_zone')]
    assert len(a)==len(b)==30
    va,vb=st.variance(a)/30,st.variance(b)/30
    mean=.5*(st.mean(a)+st.mean(b));se=.5*math.sqrt(va+vb)
    df=(va+vb)**2/(va*va/29+vb*vb/29) if va+vb else None
    half=tcrit(df)*se if df else None
    return dict(mean=mean,se=se,df=df,ci95=[mean-half,mean+half] if half is not None else None,zero_empirical_variance=df is None,inference_available=df is not None)

def summarize(rows):
    """Rows need episode_id/family_id/category/gap/lo/hi. Complete fixed schedule only.
    The production adapter must independently check these rows against frozen IDs,
    family/category metadata, legal-menu bounds and original game-state scoring.
    Unknown or untouched outcomes use gap=None, never zero.
    """
    assert len(rows)==960 and len({r['episode_id'] for r in rows})==960
    families={}
    for r in rows:
        assert r['lo']<=r['hi'] and (r['gap'] is None or r['lo']<=r['gap']<=r['hi'])
        families.setdefault(r['family_id'],[]).append(r)
    assert len(families)==80 and all(len(v)==12 for v in families.values())
    ncat={c:sum(v[0]['category']==c for v in families.values()) for c in ('tradeoffs','narrow_zone','no_zone')}
    assert ncat==dict(tradeoffs=30,narrow_zone=30,no_zone=20)
    point={c:[] for c in ('tradeoffs','narrow_zone')};lower={c:[] for c in point};upper={c:[] for c in point}
    missing=0
    for v in families.values():
        c=v[0]['category'];assert all(r['category']==c for r in v)
        if c=='no_zone':continue
        missing+=sum(r['gap'] is None for r in v)
        lower[c].append(st.mean(r['lo'] if r['gap'] is None else r['gap'] for r in v))
        upper[c].append(st.mean(r['hi'] if r['gap'] is None else r['gap'] for r in v))
        if all(r['gap'] is not None for r in v):point[c].append(st.mean(r['gap'] for r in v))
    l,u=stratified(lower),stratified(upper)
    return dict(missing_feasible_outcomes=missing,primary=None if missing else stratified(point),sample_legal_identification_bounds=[l['mean'],u['mean']],approximate_population_bound_ci95=[l['ci95'][0],u['ci95'][1]] if l['inference_available'] and u['inference_available'] else None,endpoint_inference_available={'lower':l['inference_available'],'upper':u['inference_available']},bound_interval_method='Two97.5percent one-sided Welch endpoint limits; Bonferroni simultaneous95percent; family normal/CLT approximation, no missing-at-random assumption.')

def planning():
    norm=st.NormalDist();z=norm.inv_cdf(.975);sensitivity=[]
    for sd in (5.56989097881395,8.,10.,12.):
        se=sd/math.sqrt(60)
        sensitivity.append(dict(family_sd=sd,normal_approx_power_gap4=norm.cdf(4/se-z)+norm.cdf(-4/se-z),reference_t95_halfwidth=tcrit(58)*se))
    reserves=[(2056+150*i+256)*2500+2048*10000+100000 for i in range(12)]
    return dict(independent_feasible_families=60,per_category=30,no_zone_families=20,episodes=960,planning_gap_points=4,planning_sd=10,power_target=.8,alpha_two_sided=.05,sensitivity=sensitivity,maximum_model_calls=11520,reserve_by_slot_nano=reserves,maximum_new_reserve_nano=960*sum(reserves),proposed_ceiling_nano=330000000000,prior_pilot_cost_nano=7891284039,observed_cost_extrapolation_nano=7891284039*960/144,normal_approximation_not_power_guarantee=True)

if __name__=='__main__':
    import json
    print(json.dumps(planning(),indent=2))
