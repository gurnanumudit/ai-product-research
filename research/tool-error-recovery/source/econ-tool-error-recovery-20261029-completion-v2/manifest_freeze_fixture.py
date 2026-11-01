"""Invented three-phase integration. Each RELEASE is frozen before its collection.
No actual collection, grading, credentials, network, hidden source, or code execution.
Historical reports are synthetic metadata; only the new reporter is exercised.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
MAIN = HERE.parent/'econ-tool-error-recovery-20261027-main-v1'
PREVIOUS = HERE.parent/'econ-tool-error-recovery-20261029-continuation-v1'
NODE = '/Users/muditgurnani/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'

def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')

def pins(root):
    return {str(p): digest(p) for p in root.rglob('*') if p.is_file()}

def load_report():
    spec = importlib.util.spec_from_file_location('completion_fixture_report', HERE/'report_completion.py')
    report = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(report)
    return report

HISTORY_JS = r'''

import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {pathToFileURL} from 'node:url';
const [base,main,root,mode]=process.argv.slice(2),old=path.join(base,'old'),fresh=path.join(base,'previous');
// Temporary invented evidence only: durability is not under test.
fs.fsyncSync=()=>{};
const {runInteraction,emptyResult}=await import(pathToFileURL(path.join(main,'interaction.mjs')));
const {Accounting:OldAccounting}=await import(pathToFileURL(path.join(main,'runtime-controls.mjs')));
const {createClient}=await import(pathToFileURL(path.join(main,'model-client.mjs')));
const {runContinuation}=await import(pathToFileURL(path.join(base,'collector.mjs')));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const write=(dir,n,v)=>{fs.mkdirSync(path.dirname(path.join(dir,n)),{recursive:true});fs.writeFileSync(path.join(dir,n),typeof v==='string'?v:JSON.stringify(v));};
const conditions=['clean','test-tool execution error','misleading success','stale test report'];
const schedule=Array.from({length:240},(_,i)=>({task_id:'BigCodeBench/'+(i===192?131:i===209?533:900000+i),condition:conditions[i%4],arms:i===192?['B','A','C']:i===209?['A','C','B']:['A','B','C'],block:Math.floor(i/20)+1}));
const tasks=schedule.map(r=>({task_id:r.task_id,instruct_prompt:'Invented task; never execute.',domain:'invented'}));
const prompts={baseline:'Invented baseline',warning:'Invented warning',action:'Invented action',format_error:'Invented format error'};
const stale=Object.fromEntries(schedule.filter(r=>r.condition==='stale test report').map(r=>[r.task_id,{status:'fail',feedback:'Invented stale'}]));
write(old,'worker.py','# invented worker');const vendors=['bigcodebench/eval/__init__.py','bigcodebench/eval/utils.py','bigcodebench/eval/_special_oracle.py'];
for(const n of vendors)write(old,'vendor/'+n,'# invented vendor');for(const t of tasks)write(old,'private/'+t.task_id.split('/')[1]+'.json','opaque invented package');
for(const [n,v]of Object.entries({'SCHEDULE.json':schedule,'TASKS.json':{selected_rows:tasks},'PROMPTS.json':prompts,'STALE-CACHE-COMPLETE.json':{reports:stale},'ROOT-RESOURCE-CLOSURE-ADDENDUM-v1.json':{all_launched_hosts_verified_closed:10},'APPROVED-CLEANUP-RESULT-v1.json':{name:'econ-tool-recovery-main-v1-20261027-10',closure_verified:true,deleted:true,verification:{empty:true},usage:null}}))write(old,n,v);
const pins=dir=>Object.fromEntries(fs.readdirSync(dir,{recursive:true,withFileTypes:true}).filter(p=>p.isFile()).map(p=>{const f=path.join(p.parentPath,p.name);return [f,hash(fs.readFileSync(f))];}));
write(old,'RELEASE.json',{files:pins(old)});write(old,'CLAIM.json',{release_sha256:hash(fs.readFileSync(path.join(old,'RELEASE.json')))});
let seq=0,oldCount=0;const oldEvents=[],account=new OldAccounting();const emit=e=>oldEvents.push({sequence:++seq,at:new Date().toISOString(),...e});emit({kind:'claim',...account.snapshot()});
function grade(writer,recoveryOld=false){return async a=>{const g={task_id:a.task_id,solution_sha256:hash(a.code),status:'fail',passed:false,test_run_valid:true,reason:'test_failure',feedback:'Invented failure',elapsed_seconds:.25,execution_uid:65534,execution_uid_cleanup_verified:true,local_synthetic_only:false,is_reference:false,evaluator_commit:'fd584be94e606dcc605a5b37c108e0a70a93ea20',timeout_seconds:60,hard_timeout_seconds:90,task_sha256:hash(fs.readFileSync(path.join(old,'private',a.task_id.split('/')[1]+'.json'))),worker_sha256:hash(fs.readFileSync(path.join(old,'worker.py'))),vendor_sha256:Object.fromEntries(vendors.map(n=>[n,hash(fs.readFileSync(path.join(old,'vendor',n)))])),tests_expected:2,tests_run:2};writer(a.label+'.command.json',{exitCode:0,stdout:JSON.stringify({task_id:a.task_id,status:'fail',test_run_valid:true,reason:'test_failure'}),stderr:''});if(recoveryOld&&a.kind==='final')throw Error('invented old retrieval failure');writer(a.label+'.grade.json',g);writer(a.label+'.retrieval.json',{method:'SDK readFileToBuffer',path:'/opt/idea19/'+a.label+'.result.json',bytes:JSON.stringify(g).length,no_grader_reexecution:true});return g;};}
async function savedModel({input,outputDir,callId},text,cost,phase){const id='gen_'+phase+'_'+callId;const response={id,model:'openai/gpt-6-luna',status:'completed',output:[{type:'message',role:'assistant',status:'completed',content:[{type:'output_text',text}]}],usage:{input_tokens:10,output_tokens:5,total_tokens:15,input_tokens_details:{cached_tokens:0},output_tokens_details:{reasoning_tokens:2}}};const receipt={data:{id,total_cost:(cost/1e9).toFixed(9),is_byok:false,provider_name:'openai',model:'openai/gpt-6-luna',tokens_prompt:10,tokens_completion:5}};
 return createClient({keyLoader:()=> 'SYNTHETIC_KEY_ONLY',fetcher:async(u,o)=>new Response(JSON.stringify(o.method==='POST'?response:receipt),{status:200})})({input,outputDir,callId});}
const results=[];let idx=0;for(const row of schedule)for(const arm of row.arms){if(idx>576){results.push(emptyResult(row,arm));idx++;continue;}const partial=idx===576,max=idx<493?3:2;const model=async({input,callId,round})=>{const text=round===1?'invented = 1\n':round<max?'{"action":"rerun"}':'{"action":"finish"}';account.reserve(callId);emit({kind:'model_intent',call_id:callId,task_id:row.task_id,arm,...account.snapshot()});oldCount++;const m=await savedModel({input,outputDir:path.join(old,'calls'),callId},text,oldCount===1647?521345:285000,'old');account.settle(callId,m.cost_nano_usd);emit({kind:'model_settled',call_id:callId,...account.snapshot()});return m;};let r;try{r=await runInteraction({row,arm,task:tasks.find(t=>t.task_id===row.task_id),prompts,staleReport:stale[row.task_id],model,grade:grade((n,v)=>write(old,n,v),partial),write:(n,v)=>write(old,n,v)});}catch(e){if(!partial)throw e;r=e.partialResult;}results.push(r);write(old,'result-'+row.task_id.split('/')[1]+'-'+arm+'.json',r);idx++;}
if(oldCount!==1647||account.settledNano!==469631345)throw Error('fixture old count/cost');emit({kind:'hold',...account.snapshot()});write(old,'EVENTS.jsonl',oldEvents.map(e=>JSON.stringify(e)).join('\n')+'\n');write(old,'HOLD.json',account.snapshot());write(old,'RESULTS.json',{results,...account.snapshot()});

'''

MOCK_CLIENT_AND_GRADER = r'''
function grade(writer,recoveryOld=false){return async a=>{const g={task_id:a.task_id,solution_sha256:hash(a.code),status:'fail',passed:false,test_run_valid:true,reason:'test_failure',feedback:'Invented failure',elapsed_seconds:.25,execution_uid:65534,execution_uid_cleanup_verified:true,local_synthetic_only:false,is_reference:false,evaluator_commit:'fd584be94e606dcc605a5b37c108e0a70a93ea20',timeout_seconds:60,hard_timeout_seconds:90,task_sha256:hash(fs.readFileSync(path.join(old,'private',a.task_id.split('/')[1]+'.json'))),worker_sha256:hash(fs.readFileSync(path.join(old,'worker.py'))),vendor_sha256:Object.fromEntries(vendors.map(n=>[n,hash(fs.readFileSync(path.join(old,'vendor',n)))])),tests_expected:2,tests_run:2};writer(a.label+'.command.json',{exitCode:0,stdout:JSON.stringify({task_id:a.task_id,status:'fail',test_run_valid:true,reason:'test_failure'}),stderr:''});if(recoveryOld&&a.kind==='final')throw Error('invented old retrieval failure');writer(a.label+'.grade.json',g);writer(a.label+'.retrieval.json',{method:'SDK readFileToBuffer',path:'/opt/idea19/'+a.label+'.result.json',bytes:JSON.stringify(g).length,no_grader_reexecution:true});return g;};}
async function savedModel({input,outputDir,callId},text,cost,phase){const id='gen_'+phase+'_'+callId;const response={id,model:'openai/gpt-6-luna',status:'completed',output:[{type:'message',role:'assistant',status:'completed',content:[{type:'output_text',text}]}],usage:{input_tokens:10,output_tokens:5,total_tokens:15,input_tokens_details:{cached_tokens:0},output_tokens_details:{reasoning_tokens:2}}};const receipt={data:{id,total_cost:(cost/1e9).toFixed(9),is_byok:false,provider_name:'openai',model:'openai/gpt-6-luna',tokens_prompt:10,tokens_completion:5}};
 return createClient({keyLoader:()=> 'SYNTHETIC_KEY_ONLY',fetcher:async(u,o)=>new Response(JSON.stringify(o.method==='POST'?response:receipt),{status:200})})({input,outputDir,callId});}

'''

HISTORY_TAIL = r'''
const {inspectCosts}=await import(pathToFileURL(path.join(main,'audit-costs.mjs')));
const oldCost=inspectCosts(old);
write(old,'ACTUAL-AUDIT.json',{accepted:true,observed_arms:576,files:{[path.join(old,'RESULTS.json')]:hash(fs.readFileSync(path.join(old,'RESULTS.json')))},accounting:oldCost.totals});
write(old,'ANALYSIS.json',{invented:true});write(old,'REPORT.md','Invented original primary report');
const todo=results.filter(r=>r.observation==='missing').map(r=>Object.fromEntries(['task_id','arm','condition','block','completion','calls','final_candidate_path'].map(k=>[k,r[k]])));
write(fresh,'AMENDMENT.json',{todo,source_results_sha256:hash(fs.readFileSync(path.join(old,'RESULTS.json'))),cap_usd:50,old_api_nano_usd:469631345,old_pending_nano_usd:0,pilot_carry_nano_usd:4091279770,old_main_infra_nano_usd:24000000000,new_infra_nano_usd:6000000000,new_max_calls:572,forecast_per_call_nano_usd:3248270,combined_projection_nano_usd:38566028025});
const previousRelease={...pins(old),...pins(fresh),[path.join(base,'collector.mjs')]:hash(fs.readFileSync(path.join(base,'collector.mjs')))};
write(fresh,'RELEASE.json',{accepted:true,phase:'continuation',independent_review_accepted:true,files:previousRelease});
const frozenPrevious=hash(fs.readFileSync(path.join(fresh,'RELEASE.json')));
const preflight=async()=>({account:{status:'active',plan:'pro'},prices:{at:new Date().toISOString()},credentials:{synthetic:true}});
let closed=0,count=0;
const hostFactory=async({number,write:writer})=>{const name='econ-tool-recovery-completion-v1-20261029-'+number;return {elapsed:()=>1,open:async()=>{if(closed!==number-10)throw Error('closure ordering');writer('block-'+number+'-DISPATCH.json',{name,timeout_ms:14400000,infrastructure_reserve_usd:2});writer('block-'+number+'-HOST.json',{name,vcpus:2,memory:4096});},prepare:async()=>{},beforeCall:async()=>{},grade:grade(writer),close:async()=>{closed++;return {name,block:number,creation_dispatched:true,creation_confirmed:true,stopped:true,deleted:true,verification:{empty:true},billable_egress_bytes:0,observed_resource_cost_upper_usd:0,infrastructure_reserve_usd:2};}};};
const ordered=schedule.flatMap(r=>r.arms.map(a=>r.task_id+'|'+a));
const client=async args=>{
 count++;const match=args.callId.match(/^task-(\d+)-([ABC])-call-(\d+)$/),index=ordered.indexOf('BigCodeBench/'+match[1]+'|'+match[2]),round=+match[3];
 const maximum=index<=610?3:2,text=round===1?'invented = 1\n':round<maximum?'{"action":"rerun"}':'{"action":"finish"}';
 if(args.callId!=='task-533-C-call-1')return savedModel(args,text,count===136?644125:265000,'previous');
 const id='gen_previous_'+args.callId,response={id,model:'openai/gpt-6-luna',status:'completed',output:[{type:'message',role:'assistant',status:'completed',content:[{type:'output_text',text}]}],usage:{input_tokens:10,output_tokens:5,total_tokens:15,input_tokens_details:{cached_tokens:0},output_tokens_details:{reasoning_tokens:2}}};
 let time=0;
 return createClient({keyLoader:()=> 'SYNTHETIC_KEY_ONLY',now:()=>time,delay:async ms=>{time+=ms;},fetcher:async(u,o)=>new Response(o.method==='POST'?JSON.stringify(response):'{}',{status:o.method==='POST'?200:404})})(args);
};
const summary=await runContinuation({home:fresh,source:old,preflight,prices:async()=>({synthetic:true}),client,hostFactory});
if(summary.results.filter(r=>r.observation==='observed').length!==628||summary.calls!==137||summary.settled_nano_usd!==36419125||summary.pending_nano_usd!==50000000)throw Error('historical fixture partition/finance');
if(hash(fs.readFileSync(path.join(fresh,'RELEASE.json')))!==frozenPrevious||JSON.parse(fs.readFileSync(path.join(fresh,'CLAIM.json'))).release_sha256!==frozenPrevious)throw Error('historical freeze changed');
write(fresh,'REPORT-CLAIM.json',{invented:true,no_replay:true});write(fresh,'REPORT-HOLD.json',{invented:true,reason:'historical generated-source classification defect',no_replay:true});
const {reconcile}=await import(pathToFileURL(path.join(main,'billing-scoped.mjs'))),id='gen_previous_task-533-C-call-1';
const receipt={data:{id,total_cost:'0.001272700',is_byok:false,provider_name:'openai',model:'openai/gpt-6-luna',tokens_prompt:10,tokens_completion:5}};
const response=JSON.parse(fs.readFileSync(path.join(fresh,'calls/task-533-C-call-1/response.json'))),charge=reconcile(response,receipt,id);
write(fresh,'POSTHOLD-RECEIPT-CHECK-v1.json',{generation_id:id,status:200,body:JSON.stringify(receipt)});
write(fresh,'POSTHOLD-CHARGE-ADDENDUM-v1.json',{charge});
write(fresh,'ROOT-LATE-FINANCIAL-ADDENDUM-v1.json',{combined_known_API_nano_usd:598602940,late_cost_nano_usd:1272700,historical_pending_reserve_retained_nano_usd:50000000,files:Object.fromEntries(['POSTHOLD-RECEIPT-CHECK-v1.json','POSTHOLD-CHARGE-ADDENDUM-v1.json'].map(n=>[path.join(fresh,n),hash(fs.readFileSync(path.join(fresh,n)))]))});
write(fresh,'ACTUAL-HOLD-REVIEW-v1.json',{accepted:false,invented:true,files:pins(fresh)});
console.log(JSON.stringify({historical_observed:628,previous_calls:137,original_calls:1647,previous_release_unchanged:true}));
'''

COLLECT_HEAD = r'''
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {pathToFileURL} from 'node:url';
const [base,main,root,mode]=process.argv.slice(2),old=path.join(base,'old'),previous=path.join(base,'previous'),fresh=process.argv[6]??path.join(base,'new');
fs.fsyncSync=()=>{};
const {runContinuation}=await import(pathToFileURL(path.join(root,'continuation.mjs')));
const {createClient}=await import(pathToFileURL(path.join(main,'model-client.mjs')));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const vendors=['bigcodebench/eval/__init__.py','bigcodebench/eval/utils.py','bigcodebench/eval/_special_oracle.py'];
'''
COLLECT_TAIL = r'''
let closed=0;
const preflight=async()=>({account:{status:'active',plan:'pro'},prices:{at:new Date().toISOString()},credentials:{synthetic:true}});
const hostFactory=async({number,write:writer})=>{const name='econ-tool-recovery-completion-v2-20261029-'+number;return {elapsed:()=>1,open:async()=>{if(closed!==number-11)throw Error('closure ordering');writer('block-'+number+'-DISPATCH.json',{name,timeout_ms:14400000,infrastructure_reserve_usd:2});writer('block-'+number+'-HOST.json',{name,vcpus:2,memory:4096});},prepare:async()=>{},beforeCall:async()=>{if(mode==='precall')throw Error('invented pre-reserve hold');},grade:grade(writer),close:async()=>{closed++;return {name,block:number,creation_dispatched:true,creation_confirmed:true,stopped:true,deleted:true,verification:mode==='closure'&&number===12?null:{empty:true},billable_egress_bytes:0,observed_resource_cost_upper_usd:0,infrastructure_reserve_usd:2};}};};
const summary=await runContinuation({home:fresh,source:old,previous,preflight,prices:async()=>({synthetic:true}),client:async args=>{
 if(args.callId==='task-533-C-call-1')throw Error('saved response POST forbidden');
 return savedModel(args,args.callId.endsWith('-1')?'invented = 1\n':'{"action":"finish"}',100,'completion');
},hostFactory});
console.log(JSON.stringify({synthetic:true,status:summary.collection_status,observed:summary.results.filter(r=>r.observation==='observed').length,new_calls:summary.calls}));
'''


def run_node(script, base, mode, destination=None):
    args = [NODE, str(script), str(base), str(MAIN), str(HERE), mode]
    if destination is not None:
        args.append(str(destination))
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout.splitlines()[-1])


class Fixture:
    """Owns only temporary invented evidence. freeze() precedes collect()."""
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix='completion-invented-freeze-')
        self.base = Path(self.temp.name).resolve()
        self.old, self.previous, self.new = (self.base/n for n in ('old', 'previous', 'new'))
        for p in (self.old, self.previous, self.new):
            p.mkdir()
        for name in ('analyze.py', 'actual_report.py', 'audit-costs.mjs', 'billing-scoped.mjs'):
            shutil.copyfile(MAIN/name, self.old/name)
        shutil.copyfile(PREVIOUS/'report_continuation.py', self.previous/'report_continuation.py')
        collector = (PREVIOUS/'continuation.mjs').read_text()
        for rel in ('./accounting.mjs', './host.mjs'):
            collector = collector.replace("'"+rel+"'", "'"+(PREVIOUS/rel).resolve().as_uri()+"'")
        for name in ('preflight.mjs', 'model-client.mjs', 'interaction.mjs', 'runtime-controls.mjs'):
            collector = collector.replace("'../econ-tool-error-recovery-20261027-main-v1/"+name+"'", "'"+(MAIN/name).as_uri()+"'")
        # Only the invented historical fixture's fixed recovery candidate hash changes.
        collector = collector.replace('e455718d03f9fa9fe897af7efa27d702c5499d9e6ac892dcafbda5a14742a816', hashlib.sha256(b'invented = 1\n').hexdigest())
        (self.base/'collector.mjs').write_text(collector)
        (self.base/'history.mjs').write_text(HISTORY_JS+HISTORY_TAIL)
        self.history = run_node(self.base/'history.mjs', self.base, 'history')
        self.historical_pins = {**pins(self.old), **pins(self.previous)}
        self.report = load_report()
        self.freeze()

    def freeze(self):
        assert not (self.new/'CLAIM.json').exists() and not (self.new/'RELEASE.json').exists()
        for name in (*self.report.IMPLEMENTATION_FILES, 'PROTOCOL.md'):
            shutil.copyfile(HERE/name, self.new/name)
        previous = json.loads((self.previous/'RESULTS.json').read_text())
        remaining = [{k:r[k] for k in ('task_id','arm','condition','block','completion','calls')} for r in previous['results'] if r['observation']=='missing']
        amendment = dict(phase='completion-v2',source_main=str(self.old),source_previous=str(self.previous),retained_observed=628,
                        source_results_sha256=digest(self.previous/'RESULTS.json'),remaining=remaining,
                        source_response_path='calls/task-533-C-call-1/response.json',source_response_sha256=digest(self.previous/'calls/task-533-C-call-1/response.json'),
                        saved_response_generation_id='gen_previous_task-533-C-call-1',late_charge_nano_usd=1272700,
                        conservative_carry_nano_usd=38648602940,new_model_call_maximum=367,inherited_forecast_capacity=1096,
                        nondecreasing_forecast_per_call_nano_usd=3248270,initial_combined_forecast_nano_usd=42208706860,
                        all_known_API_including_late_nano_usd=598602940,historical_pending_reserve_retained_nano_usd=50000000,
                        combined_cap_nano_usd=50000000000,new_hosts_maximum=2,new_infra_reserve_usd=4,prior_infra_reserves_retained_usd=34)
        save(self.new/'AMENDMENT.json', amendment)
        save(self.new/'OWNER-AUTHORIZATION.json', {'approved':True,'invented':True})
        self.prelaunch_pins = {**self.historical_pins, **pins(self.new)}
        save(self.new/'RELEASE.json', dict(accepted=True,phase='completion-v2',independent_review_accepted=True,files=self.prelaunch_pins,reviewed_files=self.prelaunch_pins))
        self.release_hash = digest(self.new/'RELEASE.json')
        self.implementation_hashes = {str(HERE/n):digest(HERE/n) for n in self.report.IMPLEMENTATION_FILES}
        assert not list(self.new.glob('*.candidate.py'))

    def branch(self, name):
        """Reuse immutable invented history, with a separately frozen new phase."""
        branch = object.__new__(Fixture)
        branch.base, branch.old, branch.previous = self.base, self.old, self.previous
        branch.new = self.base/name
        branch.new.mkdir()
        branch.report, branch.history = self.report, self.history
        branch.historical_pins = self.historical_pins
        branch.freeze()
        return branch

    def collect(self, mode='complete'):
        assert not (self.new/'CLAIM.json').exists()
        (self.base/'collect.mjs').write_text(COLLECT_HEAD+MOCK_CLIENT_AND_GRADER+COLLECT_TAIL)
        self.collection = run_node(self.base/'collect.mjs', self.base, mode, self.new)
        self.claim_hash = digest(self.new/'CLAIM.json')
        self.assert_immutable()
        return self.collection

    def assert_immutable(self):
        assert digest(self.new/'RELEASE.json') == self.release_hash
        if (self.new/'CLAIM.json').exists():
            assert json.loads((self.new/'CLAIM.json').read_text())['release_sha256'] == self.release_hash
            assert digest(self.new/'CLAIM.json') == self.claim_hash
        assert all(digest(p)==value for p,value in self.historical_pins.items())
        assert all(digest(p)==value for p,value in self.implementation_hashes.items())

    def audit(self):
        result = self.report.audit_and_report(self.new, self.old, self.previous)
        self.assert_immutable()
        return result

    def close(self):
        self.temp.cleanup()


if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv)>1 else 'complete'
    assert mode in ('complete','precall','closure')
    fixture = Fixture()
    try:
        fixture.collect(mode)
        audit = fixture.audit()
        analysis = json.loads((fixture.new/'ANALYSIS.json').read_text())
        print(json.dumps(dict(invented=True,mode=mode,accepted=audit['accepted'],observed=audit['observed_arms'],
                              new_calls=fixture.collection['new_calls'],contrasts=sum(len(s['contrasts']) for s in analysis['strata'].values()),
                              release_and_claim_unchanged=True,historical_evidence_unchanged=True)))
    finally:
        fixture.close()
