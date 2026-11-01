"""Offline public-metadata selection. No tests, solutions, or benchmark execution."""
import ast, collections, hashlib, itertools, json, random, sys
from pathlib import Path
sys.path.insert(0, '/tmp/idea19-parquet-reader')
import pyarrow.parquet as pq
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
PILOT=REPO/'workstreams/eval-harness-prompt-pilot-20261026/corrected-20261026'
SOURCE=REPO/'workstreams/eval-budget-allocation-pilot-20261017/task_selection/raw-v1/bigcodebench-v0.1.4.parquet'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='d9a4965821c9507ebdfb551c288656b2d5fe553234f5183044333ca8a4018267'
audit=json.loads((HERE/'METADATA-PREFLIGHT.json').read_text())
for name,h in audit['source_sha256'].items():
 if hashlib.sha256((REPO/name).read_bytes()).hexdigest()!=h: raise ValueError('source metadata changed: '+name)
excluded=set(audit['excluded_task_ids'])
exposure=json.loads((REPO/'workstreams/eval-harness-prompt-expanded-20261027/EXPOSURE-AUDIT.json').read_text())
lineage=json.loads((REPO/'workstreams/eval-split-review-alternatives-20261027/EXPOSURE-LINEAGE-NOTE.json').read_text())
updates={x['path']:x['current_sha256'] for x in lineage['documentation_updates']}
for name,h in exposure['evidence_sha256'].items():
 if hashlib.sha256((REPO/name).read_bytes()).hexdigest()!=updates.get(name,h): raise ValueError('exposure evidence changed: '+name)
for name in ['eval-harness-prompt-pilot-20261026/TASKS.json','eval-harness-prompt-pilot-20261026/corrected-20261026/TASKS.json','eval-harness-prompt-confirmation-20261027/TASKS.json']:
 prior=json.loads((REPO/'workstreams'/name).read_text())
 if not {r['task_id'] for r in prior['selected_rows']} <= excluded: raise ValueError('uncovered burned sample')
rows=pq.read_table(SOURCE,columns=['task_id','instruct_prompt','libs']).to_pylist()
assert len(rows)==1140 and len({r['task_id'] for r in rows})==1140
frame=sorted([r for r in rows if r['task_id'] not in excluded],key=lambda r:int(r['task_id'].split('/')[1]))
selected=random.Random(2026102801).sample(frame,40)
assert len(selected)==40 and not ({r['task_id'] for r in selected}&excluded)
rules=[('images',{'PIL','cv2','skimage','imageio'}),('text and language',{'nltk','textblob','spacy','gensim'}),('statistics and machine learning',{'scipy','sklearn','statsmodels'}),('data analysis and visualization',{'numpy','pandas','matplotlib','seaborn','bokeh','plotly'}),('web and protocols',{'requests','http','urllib','urllib3','django','flask','bs4','chardet','socket','ftplib'}),('files and system utilities',{'os','pathlib','shutil','psutil','subprocess','zipfile','tarfile','glob'})]
counts=collections.Counter();libs=collections.Counter()
for r in selected:
 r['libraries']=ast.literal_eval(r.pop('libs'))
 r['domain']=next((d for d,s in rules if s.intersection(r['libraries'])),'general Python and structured data')
 counts[r['domain']]+=1;libs.update(r['libraries'])
orders=list(itertools.permutations('ABC'))*6+[tuple(x) for x in ['ABC','BCA','CAB','ACB']]
random.Random(2026102803).shuffle(orders)
conditions=['clean','test-tool execution error','misleading success','stale test report']*10
random.Random(2026102802).shuffle(conditions)
schedule=[dict(task_id=r['task_id'],condition=c,arms=list(o),block=i//20+1) for i,(r,o,c) in enumerate(zip(selected,orders,conditions))]
outputs={'TASKS.json':dict(seed=2026102801,source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),excluded_task_ids=sorted(excluded),frame_count=len(frame),selected_rows=selected),'SCHEDULE.json':schedule,'PUBLIC-METADATA.json':dict(domains=dict(counts),library_counts=dict(sorted(libs.items())),domain_rules=[(d,sorted(s)) for d,s in rules],domain_caveat='Exploratory deterministic library precedence; not official taxonomy or quota sampling')}
for name,data in outputs.items():
 with (HERE/name).open('x') as f: json.dump(data,f,indent=2);f.write('\n')
baseline=json.loads((PILOT/'PROMPTS.json').read_text())['baseline']
prompts={'baseline':baseline,'warning':'Tools can return errors, stale results, or incorrect success messages. Verify important tool results before trusting them, for example by re-running or checking independently.','action':'Choose your next action using the test feedback. Return only one JSON object: {"action":"finish"} to finish with your current code; {"action":"rerun"} to run the tests again on unchanged code; or {"action":"revise","code":"complete replacement Python code"} to replace your code and run the tests. This decision uses one of your remaining model calls.','format_error':'Your previous response could not be used in the required format. Your current code, if any, is unchanged.'}
with (HERE/'PROMPTS.json').open('x') as f:json.dump(prompts,f,indent=2);f.write('\n')
with (HERE/'SAMPLE-FREEZE.json').open('x') as f:json.dump({'source_pins':audit['source_sha256'],'exposure_evidence_reverified':len(exposure['evidence_sha256']),'metadata_exclusions':len(excluded),'selected':40,'seed':2026102801,'allocation_seed':2026102802,'arm_order_seed':2026102803,'condition_counts':dict(collections.Counter(conditions)),'arm_order_counts':dict(collections.Counter(''.join(o) for o in orders)),'files':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in [*outputs,'PROMPTS.json','PROTOCOL.md',Path(__file__).name]},'private_source_inspected':False,'solver_calls':0},f,indent=2)
print(json.dumps(dict(frame=len(frame),selected=len(selected),pilot_overlap=0,domains=dict(counts)),indent=2))
