"""Pure deterministic negotiation engine. No network, provider, or credentials."""
import copy
import itertools
import json
import math
import sys

SCHEMA_VERSION = 1
ISSUES = ('delivery', 'support', 'payment')
BUYERS = ('neutral', 'firm', 'collaborative', 'programmed')
SELLERS = ('early', 'late', 'neutral_sol')
PRICES = tuple(range(80, 181, 5))
CONTRACTS = tuple(dict(contract_id=f'C{i:03d}', price=p, delivery=d, support=w, payment=f)
                  for i, (p, d, w, f) in enumerate(itertools.product(PRICES, range(2), range(2), range(2))))
BY_ID = {c['contract_id']: c for c in CONTRACTS}
PUBLIC_DISTRIBUTION = dict(buyer_base=list(range(110,151,5)), seller_base=list(range(80,121,5)),
                          marginal_values_and_costs=list(range(0,31,5)), outside_options=list(range(0,21,5)),
                          conditioning='Equal mixture of useful-tradeoff, narrow-agreement, and no-mutually-acceptable-deal scenarios; realized category is hidden.')


def other(actor):
    return 'seller' if actor == 'buyer' else 'buyer'


def validate_scenario(s):
    if not isinstance(s, dict) or not isinstance(s.get('scenario_id'), str):
        raise ValueError('scenario requires scenario_id')
    for actor in ('buyer', 'seller'):
        u=s[actor]
        if set(u) != {'base', 'marginals', 'outside_option'}:
            raise ValueError('invalid private utility fields')
        if type(u['base']) is not int or type(u['outside_option']) is not int:
            raise ValueError('integer utilities required')
        if not isinstance(u['marginals'], list) or len(u['marginals']) != 3 or any(type(x) is not int for x in u['marginals']):
            raise ValueError('three integer marginals required')
    return s


def gains(s, contract_id):
    c=BY_ID[contract_id]
    flags=[c[k] for k in ISSUES]
    b=s['buyer']; v=s['seller']
    ub=b['base']+sum(a*x for a,x in zip(b['marginals'],flags))-c['price']
    us=c['price']-v['base']-sum(a*x for a,x in zip(v['marginals'],flags))
    return dict(buyer_utility=ub,seller_utility=us,buyer_gain=ub-b['outside_option'],seller_gain=us-v['outside_option'],joint_gain=ub+us-b['outside_option']-v['outside_option'])


def own_gain(u, actor, contract):
    package=u['base']+sum(u['marginals'][i]*contract[k] for i,k in enumerate(ISSUES))
    return (package-contract['price'] if actor=='buyer' else contract['price']-package)-u['outside_option']


def benchmark(s):
    all_rows=[dict(contract_id=c['contract_id'],**gains(s,c['contract_id'])) for c in CONTRACTS]
    ir=[r for r in all_rows if r['buyer_gain']>=0 and r['seller_gain']>=0]
    strict=[r for r in ir if r['buyer_gain']>0 and r['seller_gain']>0]
    best=max([0]+[r['joint_gain'] for r in ir])
    differences=[a-b for a,b in zip(s['buyer']['marginals'],s['seller']['marginals'])]
    category=None
    if not ir:
        category='no_zone'
    elif best>=30 and sum(x>=10 for x in differences)>=2 and any(x<=-5 for x in differences):
        category='tradeoffs'
    elif 5<=best<=15 and strict:
        category='narrow_zone'
    return dict(category=category,ir_contract_count=len(ir),strict_ir_contract_count=len(strict),
                best_feasible_joint_gain=best,minimum_legal_buyer_gain=min(0,min(r['buyer_gain'] for r in all_rows)),
                maximum_legal_buyer_gain=max(0,max(r['buyer_gain'] for r in all_rows)))


def init(scenario,buyer_condition,seller_condition,first_mover,episode_id):
    validate_scenario(scenario)
    if buyer_condition not in BUYERS or seller_condition not in SELLERS or first_mover not in ('buyer','seller'):
        raise ValueError('unknown condition or first mover')
    if not isinstance(episode_id,str) or not episode_id:
        raise ValueError('episode ID required')
    return dict(schema_version=SCHEMA_VERSION,episode_id=episode_id,scenario=copy.deepcopy(scenario),
                buyer_condition=buyer_condition,seller_condition=seller_condition,first_mover=first_mover,
                slot=1,actor=first_mover,turn_counts=dict(buyer=0,seller=0),live_offer=None,transcript=[],terminal=None)


def reject_duplicate_keys(pairs):
    obj={}
    for key,value in pairs:
        if key in obj: raise ValueError("duplicate JSON field")
        obj[key]=value
    return obj


def parse_action(raw):
    if isinstance(raw,str):
        try:
            raw=json.loads(raw,object_pairs_hook=reject_duplicate_keys)
        except (ValueError,TypeError):
            return None,'malformed_json'
    if not isinstance(raw,dict):
        return None,'action_must_be_object'
    kind=raw.get('type')
    required={'OFFER':{'contract_id'},'ACCEPT':{'offer_id'},'QUERY':{'issue'},'WALK':set()}
    if not isinstance(kind,str) or kind not in required:
        return None,'unknown_action'
    if set(raw)-({'type','message'}|required[kind]) or not required[kind]<=set(raw):
        return None,'invalid_action_fields'
    message=raw.get('message','')
    if not isinstance(message,str) or len(message.split())>80 or len(message)>120 or any(ord(c)<32 or ord(c)>126 for c in message):
        return None,'message_requires_at_most_120_printable_ascii_chars_and_80_words'
    if len(json.dumps(message,ensure_ascii=False)[1:-1].encode('utf-8'))>120:
        return None,'message_exceeds_120_escaped_json_bytes'
    for name in required[kind]:
        if not isinstance(raw[name],str):
            return None,'action_argument_must_be_string'
    if kind=='OFFER' and raw['contract_id'] not in BY_ID:
        return None,'unknown_contract_id'
    if kind=='QUERY' and raw['issue'] not in ISSUES:
        return None,'unknown_query_issue'
    return {**raw,'message':message},None


def step(state,action):
    s=copy.deepcopy(state)
    if s['terminal'] is not None:
        raise ValueError('episode already terminal')
    actor=s['actor']; slot=s['slot']; previous=s['live_offer']
    a,error=parse_action(action)
    if error is None and slot==12 and a['type'] not in ('ACCEPT','WALK'):
        error='final_slot_accept_or_walk_only'
    if error is None and a['type']=='ACCEPT':
        if previous is None or previous['proposer']==actor or previous['offer_id']!=a['offer_id']:
            error='offer_not_live_opponent_offer'
    s['live_offer']=None
    s['turn_counts'][actor]+=1
    event=dict(slot=slot,actor=actor,action=a,valid_action=error is None,error=error)
    if error is None:
        kind=a['type']
        if kind=='ACCEPT':
            s['terminal']=dict(reason='agreement',contract_id=previous['contract_id'],accepted_by=actor)
            event['executed_contract_id']=previous['contract_id']
        elif kind=='WALK':
            s['terminal']=dict(reason='walkaway',contract_id=None,accepted_by=None)
        elif kind=='OFFER':
            offer=dict(offer_id=f"offer:{slot:02d}",proposer=actor,contract_id=a['contract_id'])
            s['live_offer']=offer
            event['offer_id']=offer['offer_id']
        elif kind=='QUERY':
            target=other(actor); idx=ISSUES.index(a['issue']); values=s['scenario'][target]['marginals']; value=values[idx]
            event['query_reply']=dict(target=target,issue=a['issue'],measure='marginal_cost' if target=='seller' else 'marginal_value',
                                       other_terms_lower=sum(x<value for j,x in enumerate(values) if j!=idx),
                                       other_terms_equal=sum(x==value for j,x in enumerate(values) if j!=idx))
    s['transcript'].append(event)
    if s['terminal'] is None and slot==12:
        s['terminal']=dict(reason='invalid_final_action' if error else 'deadline',contract_id=None,accepted_by=None)
    s['slot']=slot+1
    s['actor']=None if s['terminal'] else other(actor)
    return s


def transport_failure(state,metadata=None):
    s=copy.deepcopy(state)
    if s['terminal'] is not None:
        raise ValueError('episode already terminal')
    # Metadata is stored externally by collector; never splice unknown provider objects into public transcript.
    s['terminal']=dict(reason='transport_failure',contract_id=None,accepted_by=None)
    s['live_offer']=None
    s['actor']=None
    return s


def public_payload(state,viewpoint):
    if viewpoint not in ('buyer','seller'):
        raise ValueError('unknown viewpoint')
    u=state['scenario'][viewpoint]
    rows=[]
    for flags in itertools.product(range(2),repeat=3):
        rows.append(dict(**dict(zip(ISSUES,flags)),package_value_or_cost=u['base']+sum(a*b for a,b in zip(flags,u['marginals']))))
    # Explicit allowlist: no scenario IDs/categories, opponent condition, private opponent values or evaluator optimum.
    return dict(role=viewpoint,own_package_table=rows,own_outside_option=u['outside_option'],
                public_price_grid=list(PRICES),contract_id_rule='C{index:03d}; index=(price_index*8)+(delivery*4)+(support*2)+payment; price_index=(price-80)/5',
                flag_meanings=dict(delivery=['standard','rush'],support=['basic','extended'],payment=['immediate','net60']),
                utility_rule='package value - price - outside option' if viewpoint=='buyer' else 'price - package cost - outside option',
                public_generation_distribution=copy.deepcopy(PUBLIC_DISTRIBUTION),
                current_slot=state['slot'],maximum_slots=12,own_decisions_used=state['turn_counts'][viewpoint],
                first_mover=state['first_mover'],actor_to_act=state['actor'],live_offer=copy.deepcopy(state['live_offer']),
                transcript=copy.deepcopy(state['transcript']))


def scripted_action(state):
    if state['terminal']:
        raise ValueError('episode already terminal')
    actor=state['actor']
    condition=state['buyer_condition'] if actor=='buyer' else state['seller_condition']
    if (actor=='buyer' and condition!='programmed') or (actor=='seller' and condition not in ('early','late')):
        raise ValueError('current actor is not scripted')
    u=state['scenario'][actor] # This is the only private table used by the strategy.
    t=state['turn_counts'][actor]+1
    maximum=max(0,max(own_gain(u,actor,c) for c in CONTRACTS))
    aspiration=0.8*maximum*(1-(t-1)/5) if actor=='buyer' else maximum*(1-((t-1)/5)**(0.5 if condition=='early' else 3))
    live=state['live_offer']
    threshold=0 if state['slot']==12 else aspiration
    if live and live['proposer']!=actor and own_gain(u,actor,BY_ID[live['contract_id']])>=threshold-1e-10:
        return dict(type='ACCEPT',offer_id=live['offer_id'],message='I accept the current offer.')
    if state['slot']==12:
        return dict(type='WALK',message='No acceptable agreement at the deadline.')
    qualifying=[c for c in CONTRACTS if own_gain(u,actor,c)>=aspiration-1e-10]
    if not qualifying:
        return dict(type='WALK',message='No qualifying contract.')
    previous=next((e for e in reversed(state['transcript']) if e['actor']==other(actor) and e['valid_action'] and e['action']['type']=='OFFER'),None)
    package=BY_ID[previous['action']['contract_id']] if previous else dict(delivery=0,support=0,payment=0)
    def ordering(c):
        return (sum(c[k]!=package[k] for k in ISSUES),-c['price'] if actor=='buyer' else c['price'],c['contract_id'])
    chosen=min(qualifying,key=ordering)
    return dict(type='OFFER',contract_id=chosen['contract_id'],message='I offer this contract.')


def diagnostics(state):
    out={}
    for actor in ('buyer','seller'):
        events=[e for e in state['transcript'] if e['actor']==actor]
        offers=[e for e in events if e['valid_action'] and e['action']['type']=='OFFER']
        offer_gains=[own_gain(state['scenario'][actor],actor,BY_ID[e['action']['contract_id']]) for e in offers]
        out[actor]=dict(decisions=len(events),invalid_actions=sum(not e['valid_action'] for e in events),
                        offers=len(offers),queries=sum(e['valid_action'] and e['action']['type']=='QUERY' for e in events),
                        first_offer_contract_id=offers[0]['action']['contract_id'] if offers else None,
                        first_offer_price=BY_ID[offers[0]['action']['contract_id']]['price'] if offers else None,
                        own_gain_at_offers=offer_gains,own_gain_concessions=[a-b for a,b in zip(offer_gains,offer_gains[1:])])
    return out


def score(state):
    if not state['terminal']:
        raise ValueError('cannot score nonterminal episode')
    contract_id=state['terminal']['contract_id']
    result=gains(state['scenario'],contract_id) if contract_id else dict(buyer_utility=state['scenario']['buyer']['outside_option'],seller_utility=state['scenario']['seller']['outside_option'],buyer_gain=0,seller_gain=0,joint_gain=0)
    bench=benchmark(state['scenario'])
    scored_actions=copy.deepcopy(state['transcript'])
    for e in scored_actions:
        if e['valid_action'] and e['action']['type']=='OFFER':
            e.update(gains(state['scenario'],e['action']['contract_id']))
            e['proposed_buyer_gain']=e['buyer_gain']
            e['proposed_seller_gain']=e['seller_gain']
    return dict(episode_id=state['episode_id'],scenario_id=state['scenario']['scenario_id'],
                buyer_condition=state['buyer_condition'],seller_condition=state['seller_condition'],first_mover=state['first_mover'],
                terminal_reason=state['terminal']['reason'],executed_contract_id=contract_id,
                **result,any_deal=contract_id is not None,mutually_beneficial=contract_id is not None and result['buyer_gain']>=0 and result['seller_gain']>=0,
                mutually_strict_gain=contract_id is not None and result['buyer_gain']>0 and result['seller_gain']>0,
                buyer_harm=result['buyer_gain']<0,seller_harm=result['seller_gain']<0,
                best_feasible_joint_gain=bench['best_feasible_joint_gain'],
                efficiency_ratio=result['joint_gain']/bench['best_feasible_joint_gain'] if bench['best_feasible_joint_gain']>0 else None,
                missing_strategic_gain_bounds=[bench['minimum_legal_buyer_gain'],bench['maximum_legal_buyer_gain']],
                slot_count=len(state['transcript']),actions=scored_actions,diagnostics=diagnostics(state))


def dispatch(request):
    op=request['op']
    if op=='init':
        return init(**{k:request[k] for k in ('scenario','buyer_condition','seller_condition','first_mover','episode_id')})
    if op=='step': return step(request['state'],request['action'])
    if op=='scripted_action': return scripted_action(request['state'])
    if op=='public_payload': return public_payload(request['state'],request['viewpoint'])
    if op=='score': return score(request['state'])
    if op=='transport_failure': return transport_failure(request['state'])
    if op=='benchmark': return benchmark(request['scenario'])
    if op=='contracts': return CONTRACTS
    raise ValueError('unknown operation')

if __name__=='__main__':
    try:
        result=dispatch(json.load(sys.stdin))
        print(json.dumps(dict(ok=True,result=result),separators=(',',':'),allow_nan=False))
    except Exception as exc:
        print(json.dumps(dict(ok=False,error=f'{type(exc).__name__}: {exc}'),separators=(',',':')))
        sys.exit(1)
