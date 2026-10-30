"""Offline numerical verification of the published negotiation supplement. No network."""
from pathlib import Path
import json,sys,collections,hashlib
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'code'))
import game
import analysis_math as A

def read(name): return json.loads((HERE/name).read_text())
def equal(actual,expected,label):
    if not np.allclose(actual,expected,atol=2e-12,rtol=0):
        raise ValueError(f'{label}: {actual} != {expected}')

def main():
    manifest=read('MANIFEST.json')
    for name,digest in manifest['sha256'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=digest: raise ValueError('File changed: '+name)
    rows=read('data/episodes.json');d=read('reference/article-results.json');m=read('data/methods-and-scenarios.json')
    assert len(rows)==len({r['episode_id'] for r in rows})==2160
    blocks={b['scenario_id']:b for b in m['scenarios']};assert len(blocks)==180
    layout={};bench={};eligible=[];excluded=[]
    for c,cat in enumerate(A.CATEGORIES):
        ids=sorted(s for s,b in blocks.items() if b['category']==cat);assert len(ids)==60
        for i,sid in enumerate(ids):
            layout[sid]=(c,i);b=blocks[sid];s={k:b[k] for k in ('scenario_id','buyer','seller')}
            bench[sid]=game.benchmark(s);assert bench[sid]['category']==cat
            ir=[game.gains(s,x['contract_id']) for x in game.CONTRACTS];ir=[x for x in ir if x['buyer_gain']>=0 and x['seller_gain']>=0]
            if ir:
                (eligible if max(x['buyer_gain'] for x in ir)==max(x['seller_gain'] for x in ir) else excluded).append(sid)
    assert len(eligible)==107 and len(excluded)==13
    cube=np.zeros((3,60,4,3),dtype=np.int64);lower=cube.copy();upper=cube.copy()
    for r in rows:
        sid=r['scenario_id'];b=blocks[sid];assert r['category']==b['category'] and r['first_mover']==b['first_mover']
        s={k:b[k] for k in ('scenario_id','buyer','seller')}
        true=game.gains(s,r['executed_contract_id']) if r['executed_contract_id'] else dict(buyer_gain=0,seller_gain=0,joint_gain=0)
        assert all(r[k]==true[k] for k in ('buyer_gain','seller_gain','joint_gain'))
        assert not r['infrastructure_affected'] or r['executed_contract_id'] is None
        c,i=layout[sid];ib=A.BUYERS.index(r['buyer_condition']);iv=A.SELLERS.index(r['seller_condition'])
        cube[c,i,ib,iv]=r['buyer_gain']
        lower[c,i,ib,iv]=bench[sid]['minimum_legal_buyer_gain'] if r['infrastructure_affected'] else r['buyer_gain']
        upper[c,i,ib,iv]=bench[sid]['maximum_legal_buyer_gain'] if r['infrastructure_affected'] else r['buyer_gain']
    assert sum(r['any_deal'] for r in rows)==1308
    assert sum(r['infrastructure_affected'] for r in rows)==14
    assert sum(r['terminal_reason']=='walkaway' for r in rows)==838
    for cell in d['main']['cells']:
        rr=[r for r in rows if (r['buyer_condition'],r['seller_condition'])==(cell['buyer'],cell['seller'])];assert len(rr)==180
        for public,key in [('buyerGain','buyer_gain'),('sellerGain','seller_gain'),('jointGain','joint_gain')]:equal(sum(r[key] for r in rr)/180,cell[public],public)
        assert sum(r['any_deal'] for r in rr)==cell['agreements']
        assert sum(r['infrastructure_affected'] for r in rr)==cell['failures']
    ix=A.bootstrap_indices()
    for target in d['main']['contrasts']:
        left,right=target['id'].split('_minus_');a,b=A.BUYERS.index(left),A.BUYERS.index(right)
        point,draws=A.paired_difference(cube,cube,a,b,ix)
        equal(point,target['estimate'],target['id'])
        for level in (95,99):equal(A.interval(draws,level/100),target['ci'+str(level)],target['id'])
        for name,x,y in [('adverse',lower,upper),('opposite',upper,lower)]:
            point,draws=A.paired_difference(x,y,a,b,ix);t=target['failureBounds'][name]
            equal(point,t['estimate'],name);equal(A.interval(draws,.99),t['ci99'],name)
    subgroup_count=0
    for family,reports in d['main']['subgroups'].items():
        for name,report in reports.items():
            view={}
            if family=='seller':view={'seller':A.SELLERS.index(name)}
            elif family=='category':view={'categories':[A.CATEGORIES.index(name)]}
            elif family=='seller_by_category':
                cat,seller=name.split('/');view={'categories':[A.CATEGORIES.index(cat)],'seller':A.SELLERS.index(seller)}
            elif family=='first_mover':
                mask=np.zeros((3,60),dtype=bool)
                for sid,(c,i) in layout.items():mask[c,i]=blocks[sid]['first_mover']==name
                view={'mask':mask}
            else:raise ValueError(family)
            got=A.contrasts(cube,ix,descriptive=True,**view)
            for k,t in report['contrasts'].items():
                equal(got[k]['estimate'],t['estimate'],name);equal(got[k]['ci95'],t['ci95'],name)
            subgroup_count+=1
    assert subgroup_count==17
    pair=[r for r in rows if r['scenario_id'] in eligible and r['buyer_condition']=='neutral' and r['seller_condition']=='neutral_sol']
    public=d['roleGap']['rows'];assert [r['episode_id'] for r in pair]==[r['episode'] for r in public]
    for r,t in zip(pair,public):assert r['buyer_gain']==t['buyer'] and r['seller_gain']==t['seller'] and r['infrastructure_affected']==t['failure']
    for h in d['roleGap']['histogram']:
        rr=[r for r in public if r['gap']==h['gap']];assert len(rr)==h['count'] and sum(r['failure'] for r in rr)==h['failures']
    modes=('observed','adverse','opposite');rng=np.random.Generator(np.random.PCG64(2026102901));sums={k:np.zeros(10000,dtype=np.int64) for k in modes};values={k:[] for k in modes}
    for cat in ('tradeoffs','narrow_zone'):
        rr=[r for r in public if r['category']==cat];idx=rng.integers(len(rr),size=(10000,len(rr)))
        for name in modes:
            a=np.array([(-135 if name=='adverse' else 150) if r['failure'] and name!='observed' else r['gap'] for r in rr],dtype=np.int64)
            sums[name]+=a[idx].sum(axis=1);values[name].extend(a.tolist())
    for name in modes:
        target=d['roleGap']['estimates'][name];equal(sum(values[name])/107,target['estimate'],name)
        for level in (95,99):equal(A.interval(sums[name]/107,level/100),target['ci'+str(level)],name)
    rng=np.random.Generator(np.random.PCG64(2026102902));pts=[];boots=[];weights=[]
    for cat,n in [('tradeoffs',48),('narrow_zone',59)]:
        for mover in ('buyer','seller'):
            rr=[r for r in public if (r['category'],r['firstMover'])==(cat,mover)]
            target=d['firstMoverCheck']['strata'][cat+'__'+mover];assert len(rr)==target['n'];equal(sum(r['gap'] for r in rr)/len(rr),target['gap'],'stratum')
            x=np.array([[r['gap'],-135 if r['failure'] else r['gap'],150 if r['failure'] else r['gap']] for r in rr],dtype=np.int64)
            idx=rng.integers(len(rr),size=(10000,len(rr)));pts.append(x.sum(axis=0)/len(rr));boots.append(x[idx].sum(axis=1)/len(rr));weights.append(n/214)
    points=np.einsum('s,sm->m',weights,np.array(pts));draws=np.einsum('s,sbm->bm',weights,np.array(boots))
    for i,name in enumerate(modes):
        t=d['firstMoverCheck']['balanced_results'][name];equal(points[i],t['estimate'],name)
        for level in (95,99):equal(A.interval(draws[:,i],level/100),t['ci'+str(level)],name)
    print(json.dumps({'status':'PASS','episodes':2160,'scenario_menus':180,'matchups':12,'original_comparisons':5,'subgroup_reports':17,'role_pairs':107,'bootstrap_replicates':10000,'all_failure_sensitivities_verified':True,'classification':'post-interim amended / exploratory','network_calls':0,'numpy':np.__version__},indent=2))

if __name__=='__main__':
    if not __debug__: raise RuntimeError('Run without -O: assertions are verification checks.')
    main()
