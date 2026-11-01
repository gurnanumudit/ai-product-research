"""Compact operational metadata only; never inspect interim accuracy."""
import pathlib,json,datetime,os,argparse
p=argparse.ArgumentParser();p.add_argument('--save',action='store_true');a=p.parse_args();root=pathlib.Path(__file__).resolve().parent
read=lambda f:json.loads((root/f).read_text())
claim=read('CLAIM.json') if (root/'CLAIM.json').exists() else None
alive=False
if claim:
 try:os.kill(claim['pid'],0);alive=True
 except ProcessLookupError:pass
 except PermissionError:alive=None
es=[json.loads(l) for l in (root/'EVENTS.jsonl').read_text().splitlines()] if (root/'EVENTS.jsonl').exists() else []
fin=next((e for e in reversed(es) if 'settled_nano_usd' in e),{})
terminals=sum(e['kind']=='arm_complete' for e in es)
closures=[read(f.name) for f in root.glob('block-*-RESOURCE-CLOSURE.json')]
post_intents=len(list((root/'calls').glob('*/DISPATCH.json')))
settled_receipts=sum(type(json.loads(p.read_text()).get('cost_nano_usd')) is int for p in (root/'calls').glob('*/charge.json'))
s={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'claimed':claim is not None,'pid':claim['pid'] if claim else None,'process_present':alive,'original_retained_terminal':628,'continuation_terminal':terminals,'total_terminal':628+terminals,'assigned':720,'environment_ready':sum(e['kind']=='environment_ready' for e in es),'closure_records':len(closures),'verified_stopped_deleted_empty':sum(bool(c.get('stopped') and c.get('deleted') and (c.get('verification') or {}).get('empty')) for c in closures),'hold':(root/'HOLD.json').exists(),'complete':(root/'COLLECTION-COMPLETE.json').exists(),'report_claim':(root/'REPORT-CLAIM.json').exists(),'latest_event_at':es[-1]['at'] if es else None,'accounting':{k:fin.get(k) for k in ['calls','settled_nano_usd','pending_nano_usd','retained_carry_nano_usd','forecast_per_call_nano_usd','remaining_call_capacity','whole_completion_projection_nano_usd','next_physical_reserve_total_nano_usd']},'note':'Terminal counts are not success or valid-code counts. Retained carry includes old API and all old reserves plus new4USDinfra and retainedhistorical.05buffer. Unknown reserves are not activecalls.'}
s['request_counts']={'reserved_attempts':fin.get('calls',0),'physical_post_intents':post_intents,'settled_receipts':settled_receipts,'proven_pre_reservation_failures':sum(e['kind']=='model_pre_dispatch_hold' for e in es)}
if a.save:
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 with (root/f'MONITOR-{stamp}.json').open('x') as f:json.dump(s,f,indent=2);f.write('\n')
print(json.dumps(s))
